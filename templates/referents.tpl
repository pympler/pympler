%for name, (ref, obj, size) in referents.items():
    <div class="referents">
        <a class="expand_ref" id="{{ref}}" href="#">
            <span class="local_name">{{name}}</span>
            <span class="local_type">{{type(obj)}}</span>
            <span class="local_size">{{size}}</span>
            <span class="local_value">{{repr(obj)}}</span>
        </a>
        <span id="children_{{ref}}"/>
    </div>
%end            
