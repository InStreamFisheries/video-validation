## USING THE VIDEO VALIDATION SOFTWARE

Keep in mind that this layout is subject to change, this document will try to be up to date but some layout positioning may shift.
Opening the application for the first time will present you with this window. Here you can select drives, find a specific file for validation, and play footage from all cameras.

 <img width="184" alt="Video Validation 0 1 0_GKwPVAzqgm" src="https://github.com/user-attachments/assets/e4eb31d3-00b2-4729-87ec-f833b24c92a2">

## STEP BY STEP PROCESS, FINDING FOOTAGE
•	After opening the application, click the `Select Drive` button
•	Find your `REC` folder from your directory: 

<img width="472" alt="WINWORD_nTi8ZIKhgA" src="https://github.com/user-attachments/assets/13ebe176-7030-4a3f-8673-dd2807686aea">


Some things to note:
-	File format is important, the drives have a specific hierarchy for how they are presented.
-	The name of the drive does NOT matter.
-	The folder the application is looking for is called `REC`.
-	The subfolders should be named based on the cameras. `CAMX` (x being the number of the camera.)
- Within the camera folder, you should have ten minute chunks of footage, all written in a specific format. `CAMX_YYYYMMDD_HHMM` (CAMX where X is the camera number, YYYY is year, MM is month, DD is day, HH is the hour in a 24h format, and MM is minute.)
- All of this is set before the drive is sent out for validation, but should be looked over just in case.

•	Once the folder is selected, verify the appropriate folder is checked after the file folder window closes.
•	Click through the dropdown menus to choose a file based on what is in the drive.
•	Click `Play Selected` to start playback. A new window will open and playback should begin immediately.
 
## USING THE VIDEO PLAYER

![python_inbXHBdbfN](https://github.com/user-attachments/assets/961c0129-908f-4fb3-8a52-573dcb4dd06c)

 
After choosing a file, a new window will open, and playback will begin immediately. These files are saved in ten-minute chunks, and your controls will be kept in that bottom-right quadrant. 
All your main controls are in this quadrant, with some things to note:
•	`Stop` will close the current playback window and bring you back to the navigation menu
•	Speeds will affect all cameras, and to revert to the original speed you must click `1x`
•	There is a plan for a seek bar now, but is not in as of version 0.1.0
 
## TROUBLESHOOTING
One thing to note is you may be greeted with a playback window that looks like so:  

![Video Validation 0 1 0_Ogm0bkV9UX](https://github.com/user-attachments/assets/15aa65c5-b1ef-4930-baf2-9461ecb45185)


This means that the program failed to find one or more of the cameras, so you may have a file naming issue with one of them. Usually this means that one of the cameras saved the name a second later than the others, and skipped to the next minute (`11:55:59` vs `11:56:00`.) To fix this, adjust the name of the video so all three have the same timestamp (`CAMX_YYYYMMDD_HHMM.mp4`) (just change the HHMM to be the same) and the footage is synced.
Sometimes, when closing the application through the `X` at the top, you may find that it does not close properly. Please force quit the application if so to start over and return to the navigation menu.

Please contact your project lead to report any issues or feature requests for this program. 

