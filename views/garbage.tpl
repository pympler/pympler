%include header category='Garbage', title='Garbage' 
<h1>Garbage</h1>
<table id="tdata">
    <thead>
        <tr>
            <th>id</th>
            <th class="num">size</th>
            <th>type</th>
            <th>representation</th>
        </tr>
    </thead>
    <tbody>
    %for o in objects:
        <tr>
            <td>{{'0x%08x' % o.id}}</td>
            <td class="num">{{o.size}}</td>
            <td>{{o.type}}</td>
            <td>{{o.str}}</td>
        </tr>
    %end
    </tbody>
</table>

<h2>Reference cycles</h2>
<ul>
%for n in range(cycles):
    <li><a href="#{{n}}">{{n}}</a></li>
%end
</ul>
%for n in range(cycles):
    <img src="/garbage/graph/{{n}}"/>
    <a name="{{n}}"></a><br/>
%end

%include footer
