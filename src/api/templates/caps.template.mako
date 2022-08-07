<?xml version="1.0" encoding="UTF-8" ?>\
<caps>
    <server appversion="${app_version}" version="${api_version}" email="${email}"/>
    <limits max="50000" default="50000"/>
    <registration available="no" open="no"/>
    <searching>
        <search available="yes"/>
        <tv-search available="yes" supportedParams="q,season,ep,cat,limit,offset,rid,tvdbid,tvmazeid,imdbid,traktid"/>
    </searching>
    <categories>
        % for category in categories:
            <category id="${category.id}" name="${category.name}">
                % for subcategory in category.children:
                    <subcat id="${subcategory.id}" name="${subcategory.name}"/>
                % endfor
            </category>
        % endfor
    </categories>
</caps>