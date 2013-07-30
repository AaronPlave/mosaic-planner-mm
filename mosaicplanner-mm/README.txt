Quick README for MosaicPlanner with Micro-manager

#Installation

No additional 3rd party libraries are needed (I think). To run, place all of the files and folders inside the micromanager root  directory (something like C:/Program Files/Micro-Manager-1.4/). Launch with MosaicPlannerMOD.py. Note, you must have a microscope configuration from Micro-Manager already made. This program has only been used successfully on a 32-bit Windows OS, but should (in theory) work on other operating systems, assuming you can get your scope drivers to work.

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



#Known issues:
-Needs more testing of main functions. Most work well, but occasionally there are weird results.
-More to come since many more exist.


Also need to configure gitignore to ignore *.pyc
