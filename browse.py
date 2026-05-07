from do_request.request_main import do_request
from utils.utils import handle_empty_directory
from utils.url_handling import build_url

import xbmcplugin
import xbmcgui
def browse_menu(media_type, id, jellyseer_client, sonarr_client, settings, addon_handle, season = -1, episode = -1):
    if media_type != "tv":
        do_request(media_type, id, settings, jellyseer_client, addon_handle , sonarr_client, season, episode)
        return
    try:
        data = jellyseer_client.api_request(f"/tv/{id}")
        name = data.get("name")
    except:
        return
    selected = xbmcgui.Dialog().select(name, ["Request", "Browse"])
    if selected == -1:
        handle_empty_directory(addon_handle)
        return
    elif selected == 0:
        do_request(media_type, id, settings, jellyseer_client, addon_handle , sonarr_client, season, episode)
        handle_empty_directory(addon_handle)
        return
    browse_handle_season(id, data, addon_handle)

def browse_handle_season(id, data, addon_handle):
    try:
        seasons =data.get("seasons")
    except:
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
        return
    xbmcplugin.setContent(addon_handle, 'seasons')
    for season in seasons:
        list_item = xbmcgui.ListItem(label = season.get("name"))
        list_item.setInfo("video",  {'title': season.get("name"), "season": season.get("seasonNumber"), 'mediatype': 'season'})
        xbmcplugin.addDirectoryItem(addon_handle, build_url({"mode": "browse_handle_episodes", "id": id, "season": season.get("seasonNumber")}) , list_item, True)
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)  

def browse_handle_episodes(id, season, jellyseer_client, addon_handle):
    try:
        episodes = jellyseer_client.api_request(f"/tv/{id}/season/{season}").get("episodes", [])
    except:
        return
    xbmcplugin.setContent(addon_handle, 'episodes')
    for ep in episodes:
        list_item = xbmcgui.ListItem(label=ep.get("name"))
        list_item.setInfo("video",  {'title': ep.get("name"), "episode": ep.get("episodeNumber"), "season": season,  'plot': ep.get("overview"), 'mediatype': 'episode'})
        list_item.setArt({'icon': ep.get("stillPath")})
        xbmcplugin.addDirectoryItem(addon_handle, build_url({"mode": "request", "season": season, "type": "tv", "episode": ep.get("episodeNumber"), "id": id, "go_back": True }), list_item, False)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_EPISODE)
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)    
    