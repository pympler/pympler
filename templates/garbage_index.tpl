%include header category='Garbage', title='Garbage' 
<h1>Garbage - Overview</h1>

<p>TODO: short garbage description, collectable/incollectable</p>

<p>{{len(graphs)}} reference cycles:</p>

<table class="tdata">
    <tbody>
    %for graph in graphs:
        <tr>
            <td><a href="/garbage/{{graph.index}}">Cycle {{graph.index}}</a></td>
            <td class="num">{{len(graph.metadata)}}</td>
        </tr>
    %end
    </tbody>
</table>

%include footer
