%include header category='Tracker', title='Tracked objects' 

%from pympler.util.stringutils import pp, pp_timestamp
%from pympler.util.compat import dumps

<h1>Tracked objects</h1>

%if snapshots:

    <h2>Memory distribution over time</h2>

    <div id="memory_chart" style="width:100%; height: {{len(snapshots)*16+100}}px">
        Please activate Javascript to view the chart.
    </div>

    <script type="text/javascript" src="/static/highcharts.js"></script>
    <script type="text/javascript">
        function format_size(value) {
            var suffix = ['Byte', 'KB', 'MB', 'GB'];
            var suffix_index = 0;
            while (value > 10000 && suffix_index < suffix.length) {
                value = Math.round(value / 1000);
                suffix_index += 1;
            }
            return value.toLocaleString() + ' ' + suffix[suffix_index];
        }
        
        var chart;
        $(document).ready(function() {
            chart = new Highcharts.Chart({
                chart: {
                    renderTo: 'memory_chart',
                    defaultSeriesType: 'bar'
                },
                title: {
                    text: 'Process memory distribution per snapshot'
                },
                xAxis: {
                    categories: {{!dumps([sn.label for sn in snapshots])}},
                },
                yAxis: {
                    min: 0,
                    title: {
                        text: 'Allocated memory [Bytes]'
                    }
                },
                legend: {
                    backgroundColor: '#FFFFFF',
                    reversed: true
                },
                tooltip: {
                    formatter: function() {
                        return ''+
                             this.series.name +': ' + format_size(this.y);
                    }
                },
                plotOptions: {
                    bar: {
                        borderWidth: 0,
                        groupPadding: 0.1,
                        shadow: false,
                    },
                    series: {
                        animation: false,
                        stacking: 'normal'
                    }
                },
                series: [
                    % for name, series in timeseries[::-1]:
                        {
                            name: '{{name}}',
                            data: {{series}},
                        },
                    % end
                ],
            });
        });
    </script>

    <h2>Snapshots statistics</h2>

    %for sn in snapshots:
        <h3>{{sn.desc or 'Untitled'}} snapshot at {{pp_timestamp(sn.timestamp)}}</h3>
        <table class="tdata">
            <thead>
                <tr>
                    <th width="20%">Class</th>
                    <th width="20%" class="num">Instance #</th>
                    <th width="20%" class="num">Total</th>
                    <th width="20%" class="num">Average size</th>
                    <th width="20%" class="num">Share</th>
                </tr>
            </thead>
            <tbody>
                %cnames = list(sn.classes.keys())
                %cnames.sort()
                %for cn in cnames:
                    %data = sn.classes[cn]
                    <tr>
                        <td><a href="/tracker/class/{{cn}}">{{cn}}</a></td>
                        <td class="num">{{data['active']}}</td>
                        <td class="num">{{pp(data['sum'])}}</td>
                        <td class="num">{{pp(data['avg'])}}</td>
                        <td class="num">{{'%3.2f%%' % data['pct']}}</td>
                    </tr>
                %end            
            </tbody>
        </table>

        %if sn.system_total.available:
            <h4>Process memory</h4>

            <table class="tdata">
                <thead>
                    <tr>
                        <th>Type</th>
                        <th class="num">Size</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Virtual memory size</td>
                        <td class="num">{{pp(sn.system_total.vsz)}}</td>
                    </tr>
                    <tr>
                        <td>Resident set size</td>
                        <td class="num">{{pp(sn.system_total.rss)}}</td>
                    </tr>
                    <tr>
                        <td>Pagefaults</td>
                        <td class="num">{{sn.system_total.pagefaults}}</td>
                    </tr>
                    %for key, value in sn.system_total.os_specific:
                        <tr>
                            <td>{{key}}</td>
                            <td class="num">{{value}}</td>
                        </tr>
                    %end            
                </tbody>
            </table>
        %end
    %end

%else:

    <p>No objects are currently tracked. Consult the Pympler documentation for
    instructions of how to use the classtracker module.</p>

%end

%include footer
