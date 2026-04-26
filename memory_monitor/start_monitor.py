"""
Pympler Memory Monitor 启动脚本

快速启动内存监控服务。
"""

import sys
import argparse
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    parser = argparse.ArgumentParser(
        description="Pympler Memory Monitor - 基于FastAPI的内存监控服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python start_monitor.py                    # 使用默认配置启动
  python start_monitor.py --host 0.0.0.0    # 绑定所有网络接口
  python start_monitor.py --port 9000        # 使用指定端口
  python start_monitor.py --debug            # 启用调试模式
        """
    )
    
    parser.add_argument(
        "--host", "-H",
        default="localhost",
        help="绑定的主机地址 (默认: localhost)"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8080,
        help="监听端口 (默认: 8080)"
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="启用调试模式"
    )
    parser.add_argument(
        "--reload", "-r",
        action="store_true",
        help="启用自动重载 (开发模式)"
    )
    parser.add_argument(
        "--background", "-b",
        action="store_true",
        help="后台运行 (仅输出日志)"
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=1,
        help="工作进程数 (默认: 1)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Pympler Memory Monitor")
    print("基于FastAPI的轻量级内存监控服务")
    print("=" * 60)
    print()
    
    from memory_monitor import start_monitor, start_monitor_in_background
    
    if args.background:
        print(f"[启动] 后台启动监控服务...")
        thread = start_monitor_in_background(
            host=args.host,
            port=args.port,
            log_level="debug" if args.debug else "info"
        )
        print(f"[信息] 服务已在后台启动")
        print(f"[信息] 服务地址: http://{args.host}:{args.port}")
        print(f"[信息] API文档: http://{args.host}:{args.port}/docs")
        print()
        print("[提示] 按 Ctrl+C 退出程序")
        
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[退出] 程序已停止")
    else:
        print(f"[启动] 启动监控服务...")
        print(f"[信息] 服务地址: http://{args.host}:{args.port}")
        print(f"[信息] API文档: http://{args.host}:{args.port}/docs")
        print()
        print("[提示] 按 Ctrl+C 停止服务")
        print()
        
        start_monitor(
            host=args.host,
            port=args.port,
            log_level="debug" if args.debug else "info",
            reload=args.reload
        )


if __name__ == "__main__":
    main()
