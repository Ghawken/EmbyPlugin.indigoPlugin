Hi all,

Announcing the release of an Emby Plugin for Indigo.

- Enables monitoring of a Emby Client from within Indigo (with rapid response)
- Enables Remote Control of Emby Client from within Indigo with ActionGroup Commands
- Local copies of Fanart and Thumbnail Artwork to use within refreshingURL Control Page


Download/Uptodate version:
[url]https://github.com/Ghawken/EmbyPlugin.indigoPlugin/releases/latest[/url]
or from within the plugin - Update/Force Update

For those that are unaware Emby is a Media Server solution (essentially open source) competing against Kodi (completely open source) and Plex.  
([url]https://emby.media/[/url])
Emby arguably has the best image quality through use of MadVR ([url]http://forum.doom9.org/showthread.php?t=146228[/url] - for some interesting reading/2000 page thread about image quality!)

**This Indigo Plugin needs a Emby Server Plugin installed  (which is available in the Emby Plugin Catalog - called FrontView+ API)**

See install post for instructions.

Many thanks to community - and particularly DaveL for GhostXML - which I have gutted and reused as a base here after recently getting familiar with it and  also for getting me off backside into plugin packaging rather than scripts etc.

***Details/Rationale of Implementation***

This plugin utilises a Emby Server Plugin I have written for another C# app for Emby Server.  (FrontView+API)

The downside of the approach I have taken is that we get information from a single Emby Client only set at the Server level by this Emby Server Plugin.
(but this Indigo Plugin doesn't have to authenticate & then regularly grab all session data to get info for a single client)

The upside is because the server has to do and send very little - only one little clients info - the communication is very quick and lightweight.  (my Emby Server request average 1-2ms only to complete)

For my personal use - I typically interested in monitoring one Emby Client only - but I want it quick - and this Plugin is the solution to speed.

So currently these scenarios all happen within 1/2 second or so
[i]eg[/i]. doorbell rings - lights on/Emby pauses; 
I pause Emby playback - Pause lightening scene runs 
Playback restarts --> lights off etc.  

Having even 5-20 second delay for those actions for me is a deal-breaker - hence this solution (which did require getting to grips with Emby-Server API/Plugins)

Happy to hear other thoughts - and wouldn't be too much work to enable multiple clients - but it would slow, slow, slow down the response times..
(although I could change the Emby-Server Plugin to server multiple clients as an additional solution)

Anyhow - hopefully of some value - and consider it a work in progress.


Glenn

[size=150]***Installation:***[/size]

**Step 1:**
From within Emby Server - install FrontView+API from Catalog

![](https://s28.postimg.org/vchi60o8t/Front_View_API_Server.png)



**
Step 2:**
Once FrontView+API Plugin is installed on Emby Server: 
Go to it Settings -  **Plugin - FrontView+API Settings ** to select your Emby Playback client that we will be monitoring in Indigo:
(Yes we monitor a single Emby Client only - see announcement thread about details and reason why)


![](https://s23.postimg.org/4rk2p380b/Front_View_APISettings.png)
![](https://s23.postimg.org/tm3kj5suj/Front_View_APISettings2.png)

**Step 3:**
Then or before - doesn't matter - install EmbyPlugin via download instructions - double click the indigoplugin File.

**Step 4**
Then Create a new Emby-Plugin Device
![](https://s27.postimg.org/htjqc80vn/Front_View_API_client_Details.png)

![](https://s27.postimg.org/oy1jl984z/Front_View_API_client_Selection.png)

Enter the URL for your Emby Server and the port in the format as shown above.

![](https://s27.postimg.org/6d8q0fxbn/Emby_Client_Custom_States.png)


**Usage:**

The Plugin then creates a number of custom states relating to the current status of that monitored client.
(as you can see above)

The Plugin also enables  Action Groups for Remote Control:

![](https://s29.postimg.org/ic1meuy9z/Emby_Client_Action_Groups.png)


It also creates a local copy of Fanart and Thumb artwork for use in Control Pages via Refreshing URL.

[i]/Library/Application Support/Perceptive Automation/images/EmbyPlugin/Fanart_art.png
/Library/Application Support/Perceptive Automation/images/EmbyPlugin/Thumbnail_art.png
[/i]

Also updating them to blank artwork if no file is playing.

This enables you to very easily add the artwork to ControlPages - which update with time/artwork playback/and have functional remote control buttons.
Like these two examples - I whipped together it less than 2 minutes


![](https://s24.postimg.org/3v3ipt76d/Playback_Control_Page.png)

![](https://s23.postimg.org/gz2p6blaj/Playback_Control_Page2.png)


The speed of the connection and the updates - enables very responsive lights on Pause, Lights off Playback started, Movie Scene setting etc - essentially there is no delay.


Consider this very much a work in progress - but though would post as I continue to update.





Glenn
