%include header category='Garbage', title='Garbage' 
<h1>Garbage - Overview</h1>

<p>TODO: short garbage description, collectable/incollectable</p>

<p>{{len(graphs)}} reference cycles:</p>

<table class="tdata">
    <thead>
        <tr>
            <th>Reference graph</th>
            <th># objects</th>
            <th># cycle objects</th>
            <th>Total size</th>
        </tr>
    </thead>
    <tbody>
    %for graph in graphs:
        <tr>
            <td><a href="/garbage/{{graph.index}}">Cycle {{graph.index}}</a></td>
            <td class="num">{{len(graph.metadata)}}</td>
            <td class="num">{{graph.num_in_cycles}}</td>
            <td class="num">{{graph.total_size}}</td>
        </tr>
    %end
    </tbody>
</table>

%include footer
