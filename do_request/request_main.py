import xbmcgui
import xbmcplugin

def do_request(media_type, id, settings, jellyseer_client, addon_handle, sonarr_client = None, season = -1, episode_number = -1, skip_dialog = False):
    """Handle media request with advanced options"""
    seasons_to_request = [season]
    confirm_string = ""
    cancel = False
    if not skip_dialog and media_type != "movie":
        cancel, confirm_string, media_type, seasons_to_request, episode_number = show_dialog(id, media_type, season, episode_number, jellyseer_client, sonarr_client, addon_handle) 
    if cancel:
        return

    confirm_before_request = settings.confirm_before_request()
    show_quality_profiles = settings.show_quality_profiles()
    
    seerr_type = "movie"
    if media_type != "movie":
        seerr_type = "tv"
    try:
        title_data = jellyseer_client.api_request(f"/{seerr_type}/{id}")
    except:
        return
    title = title_data.get('title') or title_data.get('name', 'this content') if title_data else 'this content'

    if media_type == "episode":
        from do_request.request_episode import request_episode
        request_episode(id, title, seasons_to_request[0], episode_number, sonarr_client, jellyseer_client, addon_handle, settings)
        return
    
    is4k = False
    if settings.enable_ask_4k():
        is4k = ask_4k(settings, title)

    if show_quality_profiles:
        quality_profile = ask_quality_profile(jellyseer_client, media_type, is4k)    
    
    if confirm_before_request:
        msg = f"Request {title} {confirm_string}"
        if is4k:
            msg += " in 4K"
        msg += "?"
        if not xbmcgui.Dialog().yesno('KodiSeerr', msg):
            xbmcplugin.endOfDirectory(addon_handle, succeeded=False) 
            return
    
    payload = {
        "mediaType": media_type,
        "mediaId": int(id),
        "is4k": is4k
    }
    
    if media_type == "tv":
        payload["seasons"] = seasons_to_request

    if quality_profile:
        payload["profileId"] = quality_profile
    
    try:
        jellyseer_client.api_request("/request", method="POST", data=payload)
        from utils.logging import notify_info
        notify_info("Request Sent!")
    except:
        return


def ask_quality_profile(jellyseer_client, media_type, is4k):
        profiles = get_quality_profiles(jellyseer_client, media_type, is4k)
        if profiles:
            profile_names = [p.get("name") for p in profiles]
            selected = xbmcgui.Dialog().select('Select Quality Profile', profile_names)
            if selected >= 0:
                return profiles[selected].get("id")
        return None

def ask_4k(settings, title):
        is4k = False
        prefs = settings.get_preferences("last_quality")
        if settings.remember_last_quality() and 'last_4k_choice' in prefs:
            is4k = prefs['last_4k_choice']
        else:
            is4k = xbmcgui.Dialog().yesno('KodiSeerr', f'Request {title} in 4K quality?')
        if settings.remember_last_quality():
            settings.save_preferences("last_quality", prefs)
        return is4k

def show_dialog(id, media_type, season, episode_number, jellyseer_client, sonarr_client, addon_handle):
     tv_request_types = []
     cancel = False
     confirm_string = ""
     return_type =  "tv"
     seasons_to_request = [season]
     if int(season) > -1:
        tv_request_types.append(f"Request this season (Season {season})")    
     if sonarr_client is not None and int(episode_number) > -1:
        tv_request_types.append(f"Request this episode (S{season}E{episode_number})")         
     tv_request_types += [ "Request all seasons", "Choose a season to request"]
     if sonarr_client is not None:
        tv_request_types.append("Choose an episode to request")     
     selected_tv_request_nr = xbmcgui.Dialog().select("Seerr Request", tv_request_types)

     if selected_tv_request_nr == -1:
         xbmcplugin.endOfDirectory(addon_handle, succeeded=False) 
         cancel = True
         return cancel, confirm_string, return_type, seasons_to_request, episode_number
     
     selected_tv_request_type = tv_request_types[selected_tv_request_nr]
     if selected_tv_request_type == f"Request this episode (S{season}E{episode_number})":
         return_type = "episode"

     elif selected_tv_request_type == f"Request this season (Season {season})":
         seasons_to_request = [season]
         confirm_string = f"Season {season}"

     elif selected_tv_request_type == f"Request all seasons":
         seasons_to_request = "all"
         confirm_string = f"(All seasons)"

     elif selected_tv_request_type == f"Choose a season to request":
         try:
            seasons = jellyseer_client.api_request(f"/tv/{id}").get("seasons", [])
         except:
             cancel = True
             return cancel, confirm_string, return_type, seasons_to_request, episode_number
         season_list = []
         for seas in seasons:
            season_list.append(str(seas.get("seasonNumber", -1)))
         selected_nr = xbmcgui.Dialog().select("Season", season_list)
         if selected_nr == -1:
             cancel = True
             return cancel, confirm_string, return_type, seasons_to_request, episode_number
         season_nr = int(season_list[selected_nr])
         seasons_to_request = [season_nr]
         confirm_string = f"Season {season_nr}"       

     elif selected_tv_request_type == "Choose an episode to request":
         try:
            seasons = jellyseer_client.api_request(f"/tv/{id}").get("seasons", [])
         except:
              cancel = True
              return cancel, confirm_string, return_type, seasons_to_request, episode_number
         season_list = []
         for seas in seasons:
             season_list.append(str(seas.get("seasonNumber", -1)))
         selected = xbmcgui.Dialog().select("Season", season_list)
         if selected == -1:
             xbmcplugin.endOfDirectory(addon_handle, succeeded=False) 
             cancel = True
             return cancel, confirm_string, return_type, seasons_to_request, episode_number
         selected_season = int(season_list[selected])
         seasons_to_request = [selected_season]
         try:
            episodes = jellyseer_client.api_request(f"/tv/{id}/season/{selected_season}").get("episodes", [])
         except:
             cancel = True
             return cancel, confirm_string, return_type, seasons_to_request, episode_number
         episode_list = []
         for ep in episodes:
             ep_nr = ep.get("episodeNumber", "")
             item = xbmcgui.ListItem(label=f"Episode {ep_nr}: {ep.get('name')}")
             item.setProperty('ep_nr', str(ep_nr))
             episode_list.append(item)
         selected = xbmcgui.Dialog().select("Episode", episode_list)
         if selected == -1:
             xbmcplugin.endOfDirectory(addon_handle, succeeded=False) 
             cancel = True
             return cancel, confirm_string, return_type, seasons_to_request, episode_number   
         episode_number = int(episode_list[selected].getProperty("ep_nr"))
         return_type = "episode"
    
     return cancel, confirm_string, return_type, seasons_to_request, episode_number

def get_quality_profiles(jellyseer_client, media_type, is4k = False):
    """Get available quality profiles from server"""
    backend_name = "sonarr"
    if media_type == "movie":
        backend_name = "radarr"
    try:
        servers = jellyseer_client.api_request(f"/service/{backend_name}")
    except:
        return []
    default_server_id = -1
    if not servers:
        return []
    for server in servers:
        if str(server.get("isDefault")) == "True":
            if is4k and not server.get("is4k", False):
                continue
            default_server_id = server.get("id", None)
            break
    if default_server_id == -1:
        return []
    try:
        profiles = jellyseer_client.api_request(f"/service/{backend_name}/{default_server_id}").get("profiles", [])
    except:
        return []
    return profiles
                                            
    
        