%include header category='Tracker', title='Tracked objects' 

%from pympler.util.stringutils import pp, pp_timestamp

<h1>Tracked objects</h1>

%if snapshots:

    <h2>Memory distribution over time</h2>

    <img src="/tracker/distribution"/>

    <h2>Snapshots statistics</h2>

    %for sn in snapshots:
        <h3>{{sn.desc or 'Untitled'}} snapshot at {{pp_timestamp(sn.timestamp)}}</h3>
        <table id="tdata">
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
                        <td>{{cn}}</td>
                        <td class="num">{{data['active']}}</td>
                        <td class="num">{{pp(data['sum'])}}</td>
                        <td class="num">{{pp(data['avg'])}}</td>
                        <td class="num">{{'%3.2f%%' % data['pct']}}</td>
                    </tr>
                %end            
            </tbody>
        </table>
    %end

%else:

    <p>No objects are currently tracked. Consult the Pympler documentation for
    instructions of how to use the tracker module. TODO: Link to local or
    online documentation.</p>

%end

%include footer
