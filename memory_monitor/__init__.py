"""
基于FastAPI的Pympler内存监控服务

提供RESTful API接口和简单的Web界面，用于监控Python应用的内存使用情况。
"""

import json
import os
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
from weakref import WeakValueDictionary

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pympler import muppy, summary, asizeof
from pympler.process import ProcessMemoryInfo, get_current_threads
from pympler.tracker import SummaryTracker
from pympler.util.stringutils import pp


class MemorySnapshot(BaseModel):
    timestamp: str
    snapshot_id: str
    total_objects: int
    total_size_bytes: int
    total_size_formatted: str
    summary: List[Dict[str, Any]]


class ObjectStats(BaseModel):
    timestamp: str
    type_name: str
    count: int
    total_size_bytes: int
    total_size_formatted: str
    avg_size_bytes: float


class LeakAnalysis(BaseModel):
    timestamp: str
    status: str
    potential_leaks: List[Dict[str, Any]]
    recommendations: List[str]


class ProcessInfo(BaseModel):
    timestamp: str
    pid: int
    rss_bytes: int
    rss_formatted: str
    vsz_bytes: int
    vsz_formatted: str
    pagefaults: int


class MemoryMonitorServer:
    def __init__(self):
        self.snapshots: Dict[str, MemorySnapshot] = {}
        self.tracker: Optional[SummaryTracker] = None
        self.id2ref: WeakValueDictionary = WeakValueDictionary()
        self.id2obj: Dict[int, Any] = {}
        self.export_dir: Path = Path.cwd() / "memory_exports"
        self.export_dir.mkdir(exist_ok=True)
        self._lock = threading.Lock()

    def _get_ref(self, obj: Any) -> str:
        oid = id(obj)
        try:
            self.id2ref[oid] = obj
        except TypeError:
            self.id2obj[oid] = obj
        return str(oid)

    def _get_obj(self, ref: str) -> Any:
        oid = int(ref)
        return self.id2ref.get(oid) or self.id2obj.get(oid)

    def create_snapshot(self, snapshot_id: Optional[str] = None) -> MemorySnapshot:
        with self._lock:
            if snapshot_id is None:
                snapshot_id = f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            objects = muppy.get_objects()
            total_size = muppy.get_size(objects)
            sum_data = summary.summarize(objects)
            
            formatted_summary = []
            for row in sum_data:
                formatted_summary.append({
                    "type": row[0],
                    "count": row[1],
                    "size_bytes": row[2],
                    "size_formatted": pp(row[2])
                })
            
            formatted_summary.sort(key=lambda x: x["size_bytes"], reverse=True)
            
            snapshot = MemorySnapshot(
                timestamp=datetime.now().isoformat(),
                snapshot_id=snapshot_id,
                total_objects=len(objects),
                total_size_bytes=total_size,
                total_size_formatted=pp(total_size),
                summary=formatted_summary
            )
            
            self.snapshots[snapshot_id] = snapshot
            return snapshot

    def get_object_stats(self, limit: int = 20) -> List[ObjectStats]:
        objects = muppy.get_objects()
        sum_data = summary.summarize(objects)
        
        stats = []
        for row in sum_data:
            stat = ObjectStats(
                timestamp=datetime.now().isoformat(),
                type_name=row[0],
                count=row[1],
                total_size_bytes=row[2],
                total_size_formatted=pp(row[2]),
                avg_size_bytes=row[2] / row[1] if row[1] > 0 else 0
            )
            stats.append(stat)
        
        stats.sort(key=lambda x: x.total_size_bytes, reverse=True)
        return stats[:limit]

    def analyze_leaks(self, baseline_snapshot_id: Optional[str] = None) -> LeakAnalysis:
        with self._lock:
            if self.tracker is None:
                self.tracker = SummaryTracker()
                return LeakAnalysis(
                    timestamp=datetime.now().isoformat(),
                    status="tracker_initialized",
                    potential_leaks=[],
                    recommendations=[
                        "SummaryTracker已初始化，请执行一些操作后再次调用此接口进行泄漏分析",
                        "或者创建两个快照进行比较分析"
                    ]
                )
            
            diff = self.tracker.diff()
            
            potential_leaks = []
            for row in diff:
                if row[1] > 0 or row[2] > 0:
                    potential_leaks.append({
                        "type": row[0],
                        "added_count": row[1],
                        "added_size_bytes": row[2],
                        "added_size_formatted": pp(row[2])
                    })
            
            recommendations = []
            if potential_leaks:
                potential_leaks.sort(key=lambda x: x["added_size_bytes"], reverse=True)
                for leak in potential_leaks[:5]:
                    if leak["added_count"] > 0:
                        recommendations.append(
                            f"类型 '{leak['type']}' 增加了 {leak['added_count']} 个对象，"
                            f"增加内存 {leak['added_size_formatted']}"
                        )
            
            if not recommendations:
                recommendations.append("未检测到明显的内存泄漏迹象")
            
            return LeakAnalysis(
                timestamp=datetime.now().isoformat(),
                status="completed",
                potential_leaks=potential_leaks,
                recommendations=recommendations
            )

    def compare_snapshots(self, snap1_id: str, snap2_id: str) -> Dict[str, Any]:
        if snap1_id not in self.snapshots or snap2_id not in self.snapshots:
            raise HTTPException(
                status_code=404,
                detail=f"快照不存在: {snap1_id if snap1_id not in self.snapshots else snap2_id}"
            )
        
        snap1 = self.snapshots[snap1_id]
        snap2 = self.snapshots[snap2_id]
        
        snap1_types = {s["type"]: s for s in snap1.summary}
        snap2_types = {s["type"]: s for s in snap2.summary}
        
        all_types = set(snap1_types.keys()).union(set(snap2_types.keys()))
        
        diff_summary = []
        for type_name in all_types:
            s1 = snap1_types.get(type_name, {"count": 0, "size_bytes": 0})
            s2 = snap2_types.get(type_name, {"count": 0, "size_bytes": 0})
            
            count_diff = s2["count"] - s1["count"]
            size_diff = s2["size_bytes"] - s1["size_bytes"]
            
            if count_diff != 0 or size_diff != 0:
                diff_summary.append({
                    "type": type_name,
                    "count_1": s1["count"],
                    "count_2": s2["count"],
                    "count_diff": count_diff,
                    "size_1_bytes": s1["size_bytes"],
                    "size_2_bytes": s2["size_bytes"],
                    "size_diff_bytes": size_diff,
                    "size_diff_formatted": pp(size_diff)
                })
        
        diff_summary.sort(key=lambda x: abs(x["size_diff_bytes"]), reverse=True)
        
        return {
            "snapshot_1": {
                "id": snap1_id,
                "timestamp": snap1.timestamp,
                "total_objects": snap1.total_objects,
                "total_size_bytes": snap1.total_size_bytes
            },
            "snapshot_2": {
                "id": snap2_id,
                "timestamp": snap2.timestamp,
                "total_objects": snap2.total_objects,
                "total_size_bytes": snap2.total_size_bytes
            },
            "diff": {
                "total_objects_diff": snap2.total_objects - snap1.total_objects,
                "total_size_diff_bytes": snap2.total_size_bytes - snap1.total_size_bytes,
                "total_size_diff_formatted": pp(snap2.total_size_bytes - snap1.total_size_bytes),
                "by_type": diff_summary[:50]
            }
        }

    def get_process_info(self) -> ProcessInfo:
        pmi = ProcessMemoryInfo()
        return ProcessInfo(
            timestamp=datetime.now().isoformat(),
            pid=pmi.pid,
            rss_bytes=pmi.rss,
            rss_formatted=pp(pmi.rss),
            vsz_bytes=pmi.vsz,
            vsz_formatted=pp(pmi.vsz),
            pagefaults=pmi.pagefaults
        )

    def export_to_json(self, data: Any, filename: Optional[str] = None) -> str:
        if filename is None:
            filename = f"memory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = self.export_dir / filename
        
        def convert_to_dict(obj):
            if hasattr(obj, '__dict__'):
                return obj.__dict__
            elif isinstance(obj, list):
                return [convert_to_dict(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_to_dict(v) for k, v in obj.items()}
            return obj
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(convert_to_dict(data), f, ensure_ascii=False, indent=2, default=str)
        
        return str(filepath)

    def list_exports(self) -> List[Dict[str, Any]]:
        exports = []
        for f in self.export_dir.glob("*.json"):
            stat = f.stat()
            exports.append({
                "filename": f.name,
                "size_bytes": stat.st_size,
                "size_formatted": pp(stat.st_size),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
        exports.sort(key=lambda x: x["created"], reverse=True)
        return exports

    def reset_tracker(self):
        with self._lock:
            self.tracker = SummaryTracker()
            self.id2ref.clear()
            self.id2obj.clear()


monitor_server = MemoryMonitorServer()
app = FastAPI(
    title="Pympler Memory Monitor API",
    description="基于FastAPI的Pympler内存监控服务，提供内存快照、对象统计、泄漏分析等功能",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"
TEMPLATE_DIR = Path(__file__).parent / "templates"


@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = TEMPLATE_DIR / "index.html"
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="""
    <html>
        <head>
            <title>Pympler Memory Monitor</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                h1 { color: #333; }
                .api-list { list-style: none; padding: 0; }
                .api-list li { margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 5px; }
                .api-list a { color: #0066cc; text-decoration: none; }
            </style>
        </head>
        <body>
            <h1>Pympler Memory Monitor API</h1>
            <p>访问 <a href="/docs">/docs</a> 查看API文档</p>
            <h2>可用接口:</h2>
            <ul class="api-list">
                <li><a href="/api/process">/api/process</a> - 获取进程内存信息</li>
                <li><a href="/api/snapshot">/api/snapshot</a> - 创建内存快照</li>
                <li><a href="/api/snapshots">/api/snapshots</a> - 列出所有快照</li>
                <li><a href="/api/stats">/api/stats</a> - 获取对象统计</li>
                <li><a href="/api/leaks">/api/leaks</a> - 泄漏分析</li>
                <li><a href="/api/exports">/api/exports</a> - 列出导出文件</li>
            </ul>
        </body>
    </html>
    """)


@app.get("/api/process", response_model=ProcessInfo)
async def get_process_info():
    return monitor_server.get_process_info()


@app.post("/api/snapshot", response_model=MemorySnapshot)
async def create_snapshot(snapshot_id: Optional[str] = Query(None, description="可选的快照ID")):
    return monitor_server.create_snapshot(snapshot_id)


@app.get("/api/snapshots")
async def list_snapshots():
    return {
        "count": len(monitor_server.snapshots),
        "snapshots": [
            {
                "snapshot_id": snap.snapshot_id,
                "timestamp": snap.timestamp,
                "total_objects": snap.total_objects,
                "total_size_formatted": snap.total_size_formatted
            }
            for snap in monitor_server.snapshots.values()
        ]
    }


@app.get("/api/snapshot/{snapshot_id}")
async def get_snapshot(snapshot_id: str):
    if snapshot_id not in monitor_server.snapshots:
        raise HTTPException(status_code=404, detail=f"快照不存在: {snapshot_id}")
    return monitor_server.snapshots[snapshot_id]


@app.get("/api/stats")
async def get_object_stats(limit: int = Query(20, ge=1, le=100, description="返回前N个最大的类型")):
    return monitor_server.get_object_stats(limit)


@app.get("/api/leaks", response_model=LeakAnalysis)
async def analyze_leaks(baseline_snapshot_id: Optional[str] = Query(None)):
    return monitor_server.analyze_leaks(baseline_snapshot_id)


@app.get("/api/compare")
async def compare_snapshots(
    snap1: str = Query(..., description="第一个快照ID"),
    snap2: str = Query(..., description="第二个快照ID")
):
    return monitor_server.compare_snapshots(snap1, snap2)


@app.post("/api/export/snapshot/{snapshot_id}")
async def export_snapshot(snapshot_id: str, filename: Optional[str] = None):
    if snapshot_id not in monitor_server.snapshots:
        raise HTTPException(status_code=404, detail=f"快照不存在: {snapshot_id}")
    
    snapshot = monitor_server.snapshots[snapshot_id]
    filepath = monitor_server.export_to_json(snapshot, filename)
    
    return {
        "success": True,
        "message": f"快照已导出到: {filepath}",
        "filepath": filepath,
        "filename": os.path.basename(filepath)
    }


@app.post("/api/export/current")
async def export_current_state(filename: Optional[str] = None):
    snapshot = monitor_server.create_snapshot()
    filepath = monitor_server.export_to_json(snapshot, filename)
    
    return {
        "success": True,
        "message": f"当前状态已导出到: {filepath}",
        "filepath": filepath,
        "filename": os.path.basename(filepath),
        "snapshot_id": snapshot.snapshot_id
    }


@app.get("/api/exports")
async def list_exports():
    return {
        "count": len(monitor_server.list_exports()),
        "exports": monitor_server.list_exports()
    }


@app.get("/api/exports/{filename}")
async def download_export(filename: str):
    if not filename.endswith('.json'):
        filename += '.json'
    
    filepath = monitor_server.export_dir / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
    
    return FileResponse(
        path=str(filepath),
        media_type="application/json",
        filename=filename
    )


@app.post("/api/reset")
async def reset_tracker():
    monitor_server.reset_tracker()
    return {"message": "Tracker已重置，所有缓存已清除"}


def start_monitor(host: str = "localhost", port: int = 8080, **kwargs):
    import uvicorn
    uvicorn.run(app, host=host, port=port, **kwargs)


def start_monitor_in_background(host: str = "localhost", port: int = 8080, **kwargs):
    import uvicorn
    
    class ServerThread(threading.Thread):
        def __init__(self):
            super().__init__(daemon=True)
            self.config = uvicorn.Config(app, host=host, port=port, **kwargs)
            self.server = uvicorn.Server(self.config)
        
        def run(self):
            self.server.run()
        
        def stop(self):
            self.server.should_exit = True
    
    thread = ServerThread()
    thread.start()
    return thread
