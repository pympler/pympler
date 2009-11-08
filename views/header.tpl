<html>

<head>
    <title>Pympler - {{title}}</title>
    <link rel="stylesheet" type="text/css" href="static/style.css">
</head>

%navbar = [
%    ("Overview", "/"), 
%    ("Process", "/process"), 
%    ("Tracked objects", "/tracker"),
%    ("Garbage", "/garbage"),
%    ("Help", "/help")]

<body>
<div id="navbar">
    <span class="inbar">
        <ul>
            %for link, href in navbar:
                %hl = ''
                %if link == category:
                    %hl = ' class="navhome"'
                %end
                <li{{hl}}><a href="{{href}}"><span>{{link}}</span></a></li>
            %end
        </ul>
    </span>
</div>
