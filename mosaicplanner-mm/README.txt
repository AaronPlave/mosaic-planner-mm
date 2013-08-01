***FOR MOST CURRENT README + INSTALLATION + CODE PLEASE VISIT https://github.com/aplave/mosaic-planner-mm ****


README for MosaicPlanner with Micro-manager


#Introduction

This fork of Mosaic Planner extends the functionality of the vanilla version by adding in support for direct microscope and camera control via the Python wrapper for the Micro-Manager, a powerful open soured utility for interfacing with and controlling microscopes (http://valelab.ucsf.edu/~MM/MMwiki/index.php/Micro-Manager). Please note that this version of Mosaic Planner is NOT currently backwards compatible with the vanilla version, so will most likely fail to work for Axiovision projects.


#Installation

No additional 3rd party libraries are needed (I think). To run, place all of the files and folders inside the micromanager root  directory (something like C:/Program Files/Micro-Manager-1.4/). Launch with MosaicPlannerMOD.py. Note, you must have a microscope configuration from Micro-Manager already made. This program has only been used successfully on a 32-bit Windows OS, but should (in theory) work on other operating systems, assuming you can get your scope drivers to work.

If you're new to Git/Github, you can download a copy of the repository from https://github.com/aplave/mosaic-planner-mm by clicking the 'Download Zip' button on the right side of the screen. Unzip these files and continue with the installation.

This software was tested using Micro-Manager v1.4 (on 32 bit Windows XP) although newer versions of MM should be compatible, assuming no major changes to the MMcore API are made. Install Micro-Manager and configure your microscope and camera using the MM Hardware Wizard. The configuration file you generate here will be used with Mosaic Planner. Next, drag all of the files in this repository into the root Micro-Manager directory (something like C:/Program Files/Micro-Manager 1.4/ ).

Aside from the Micro-Manager components, this version of Mosaic Planner can be installed in the same manner as the vanilla version of Mosaic Planner (found here: https://code.google.com/p/smithlabsoftware/wiki/MosaicPlanner).

Run the main program with MosaicPlannerMOD.py. Once you've successfully gotten to the main window, try importing a microscope configuration file. If it works, you'll see a message like "Successfully loaded config". Otherwise, check your config file to make sure it loads in Micro-Manager, ensure that all your components are powered on and functional, and that MMcore isn't being used by and other process. It is possible that MosaicPlannerMOD.py did not exit correctly if you ran into errors, meaning that the scope may not have been unloaded from the session.

-Quick note: If you experience an error that resembles "...object has no NTBPAN attribute", you are most likely using version 1.2 of Matplotlib, which consolidated to pan attributes into one attribute. You can either fix this issue (a quick Google search should do the trick) or just use Matplotlib 1.1.




#Usage

1. First, create or load a project directory. If you choose to create a project, the program will attempt to create a new project in the selected directory. If a project already exists, the project path will just be set to the specified path. If you choose to load a project dir, the program will attempt to find the correct files and folders and then load the project.

2. Load a MM system configuration. 

3. You can change the settings in MM Settings in the upper toolbar.

4. Use your microscope to center the first slice and roughly focus.

5. Click on the camera icon with the number 1 to autofocus on the position, snap an image, and load into the canvas.

6. Center the scope on the next slice and focus.

7. Click the camera icon with the number 2 to autofocus, snap, and load the image into the canvas. Note that the previous image will be padded together with the new image, resulting in a mosaic that will be saved as mosaic.tif in your project dir.

8. Select two points and cross correlate.

9. Click the run icon to automatically acquire new images. The next position will be guessed based on the previous MosaicPlanner next position function. The stage will move to the position, the scope will autofocus, and snap and image. Then, the program will cross-correlate with a 100 default pixel (think it's pixel, not UM) window size. If successful, the image will be loaded and the next image will be acquired. If unsuccessful, larger window sizes will be used for cross-correlation. If they all fail, the program will stop. This indicates that it either reached the end or failed to find a match. 

10. You can select an image by using the icon with an image and an arrow (add nearest image to selection) and delete it using the red X button. This will remove the image and redo the mosaic + extent.

11. You can manually snap an image without autofocus by clicking the camera icon with a plus sign.

12. Your settings will be automatically saved each time you open and close the MM settings dialogue box. The settings will be loaded when you load a project, assuming you changed the default settings.


#Known issues + Future Developments:

-Needs more testing of main functions. Most work well, but occasionally there are weird results.
-cross correlation doesn't always work the first time you do a cross correllation in the very beginning. Also, the program does 2 cross-corrs by default since I've found that doing it twice leads to better results.
-Bug where the canvas doesn't refresh the position and cutout of the last point you do automatically until you select the point/any piont
-Sometimes fails when acquiring images in a manner outside of normal use cases.
-Mosaic Planner axes are a pain. Depending on your stage, the axes may not accurately reflect the actual stage axes, in which case you have to go into MosaicPlannerMOD.py and MosaicImage.py and change how the extent is handled, all the way from loading the image, setting the extent, loading/displaying highres cutouts, and cross-correlation. Should definitely figure out how to have this NOT hardcoded so that the user can play around with it easily.
-More user defined parameters and options
-Currently saves frames/points to a MicroManager compatible format, but not using the MM metadata saver, so many become outdated, but easy to update.
-stage safety features to ensure stage doesn't accidentally go too far
-focus plane corection/better autofocus
-better cross-correlation/different method of identifying slices
-better error handling for non-standard use cases
-Switch to a more robust GUI
-Backwards compatibility with vanilla Mosaic Planner
-Persistant microscope coordinates (currently resetting every time scope is powered off)
-64 bit OS compatibility + testing on different systems
-testing with different microscopes and cameras
