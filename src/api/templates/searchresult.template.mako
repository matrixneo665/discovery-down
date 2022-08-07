<?xml version="1.0" encoding="UTF-8" ?>\
<%!
    from email import utils
%>
<rss version="2.0" xmlns:newznab="http://www.newznab.com/DTD/2010/feeds/attributes/">
<channel>
    <title>Discovery Down</title>
    <description></description>
    <link></link>
    <newznab:response offset="${offset}" total="${total}"/>
    % for release in releases:
        <%
            added_date = release.added.timestamp()
            posted_date = release.posted.timestamp()

            resolution = "unknown"

            titleAppend = ""

            if (release.resolution >= 3840):
                resolution = "3840 x 2160"
                titleAppend = "4K-UHD"
            elif (release.resolution >= 1920):
                resolution = "1920x1080"
                titleAppend = "1080p"
            elif (release.resolution >= 1280):
                resolution = "1280x720"
                titleAppend = "720p"
            else:
                resolution = "852x480"
                titleAppend = "480p"

            title = "{0}.WebDL-{1}".format(release.title, titleAppend)
        %>
        <item>
            <title>${title}</title>
            <guid isPermaLink="true">${release.id}</guid>
            <link>${get_url(release.id)}</link>
            <pubDate>${utils.formatdate(added_date)}</pubDate>
            % if release.category.parent_id:
            <category>${release.category.parent.name} &gt; ${release.category.name}</category>
            % else:
            <category>${release.category.name}</category>
            % endif
            <description>${release.search_name}</description>
            <posted>${utils.formatdate(posted_date)}</posted>
            <group>${release.group.name}</group>
            <enclosure url="${get_url(release.id)}" length="${release.size}" type="application/x-nzb"></enclosure>
            <grabs>${release.grabs}</grabs>

            <newznab:attr name="category" value="${release.category.id}"/>
            % if release.category.parent_id:
            <newznab:attr name="category" value="${release.category.parent_id}"/>
            % endif
            % if release.tvshow:
                % for dbid in release.tvshow.ids:
            <newznab:attr name="${dbid.db}" value="${dbid.db_id}"/>
                % endfor
            % endif
            % if release.movie:
                % for dbid in release.movie.ids:
            <newznab:attr name="${dbid.db}" value="${dbid.db_id}"/>
                % endfor
            % endif
            <newznab:attr name="guid" value="${release.id}"/>
            <newznab:attr name="poster" value="${release.posted_by}"/>
            <newznab:attr name="usenetdate" value="${utils.formatdate(posted_date)}"/>
            <newznab:attr name="grabs" value="${release.grabs}"/>
            <newznab:attr name="group" value="${release.group.name}"/>
            <newznab:attr name="episode" value="${release.episode}"/>
            <newznab:attr name="season" value="${release.season}"/>
            <newznab:attr name="tvdbid" value="${release.tvdbid}" />
            <newznab:attr name="resolution" value="${resolution}" />
	    % if release.size:
            <newznab:attr name="size" value="${release.size}"/>
	    <size>${release.size}</size>
	    % endif
        </item>
    % endfor
    </channel>
</rss>