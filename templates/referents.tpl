%for name, (ref, obj, size) in referents.items():
    <div class="referents">
        <span class="local_name">{{name}}</span>
        <span class="local_type">{{type(obj)}}</span>
        <span class="local_size">{{size}}</span>
        <span class="local_value">{{repr(obj)}}</span>
        <a class="expand_ref" id="{{ref}}"  href="#">Expand</a>
    </div>
%end            
<script type="text/javascript">
    $(".expand_ref").click(function() {
        oid = $(this).attr("id");
        $.get("/objects/"+oid, function(data) {
            $("#"+oid).replaceWith(data);
        });
        return false;
    });
</script>
