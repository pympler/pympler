<div class="stacktrace">
    <strong>Stacktrace for thread {{threadid}}</strong>
    %for frame in stack:
        <div class="stackframe">
            <span class="filename">{{frame[1]}}</span>
            <span class="lineno">{{frame[2]}}</span>
            <span class="function">{{frame[3]}}</span>
            %if frame[4]:
                <div class="context">
                    %for line in frame[4]:
                        %if line.strip():
                            <span style="padding-left:{{len(line)-len(line.lstrip())}}em">
                                {{line.strip()}}
                            </span>
                            <br/>
                        %end
                    %end
                </div>
            %end
        </div>
    %end
    %if not stack:
        Cannot retrieve stacktrace for thread {{threadid}}.
    %end
</div>
