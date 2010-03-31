%include header category='Process', title='Process Information'
%from pympler.util.stringutils import pp

<h1>Process information</h1>

<table class="tdata">
    <tbody>
    <tr>
        <th>Virtual size:</th>
        <td class="num">{{pp(info.vsz)}}</td>
    </tr>
    <tr>
        <th>Physical memory size:</th>
        <td class="num">{{pp(info.rss)}}</td>
    </tr>
    <tr>
        <th>Major pagefaults:</th>
        <td class="num">{{info.pagefaults}}</td>
    </tr>
    %for key, value in info.os_specific:
        <tr>
            <th>{{key}}:</th>
            <td class="num">{{value}}</td>
        </tr>
    %end
    </tbody>
</table>

<h2>Thread information</h2>

<table class="tdata">
    <tbody>
    <tr>
        <th>ID</th>
        <th>Name</th>
        <th>Daemon</th>
    </tr>
    %for tinfo in threads:
        <tr>
            <td>{{tinfo.ident}}</td>
            <td>{{tinfo.name}}</td>
            <td>{{tinfo.daemon}}</td>
        </tr>
    %end
    </tbody>
</table>

%include footer
