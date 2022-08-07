<html>
<head>
<title>Add D+ Show</title>
</head>
<body>
<form method="POST" action="${postUrl}">
<label for="dUrl">D+ Url:</label>
<br />
<input type="text" width="50" name="dUrl" id="dUrl" />
<br />
<label for="tvdbId">TVDB ID: </label>
<br />
<input type="text" width="50" name="tvdbId" id="tvdbId" />

<input type="submit" text="Add Show" />
</form>
<br />
<br />
<table>
    <thead>
        <tr>
            <th>Show</th>
            <th>Seasons</th>
            <th>Episodes</th>
        </tr>
    </thead>
    <tbody>
        % for show in showData:
        <tr>
            <td>${show.title}</td>
            <td>${show.seasonCount}</td>
            <td>${show.episodeCount}</td>
        </tr>
        % endfor
    </tbody>
</table>
</body>
</html>