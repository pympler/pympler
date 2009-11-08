%include header category='Process', title='Process Information'
%from pympler.util.stringutils import pp
<table id="tdata">
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
%include footer
