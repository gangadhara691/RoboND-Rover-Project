import numpy as np
import cv2

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, rgb_thresh=(160, 160, 160)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select
def color_thresh_obj(img, rgb_thresh=(60, 60,60)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] < rgb_thresh[0]) \
                & (img[:,:,1] < rgb_thresh[1]) \
                & (img[:,:,2] < rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select
def color_thresh_roc(img, rgb_thresh=(110, 110,50)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met#&(rgb_thresh[0]+100 >img[:,:,0])\#&(rgb_thresh[1]+80 >img[:,:,1])\#&(rgb_thresh[2]+95 >img[:,:,2])
    above_thresh =  (img[:,:,0] > rgb_thresh[0])\
    & (img[:,:,1] > rgb_thresh[1])\
    & (img[:,:,2] < rgb_thresh[2]) 
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select
def color_thresh_rock(img, rgb_thresh=(120, 110,0)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh =  (img[:,:,0] > rgb_thresh[0])&(rgb_thresh[0]+100 >img[:,:,0])\
                & (img[:,:,1] > rgb_thresh[1])&(rgb_thresh[1]+80 >img[:,:,1])\
                & (img[:,:,2] > rgb_thresh[2])&(rgb_thresh[2]+95 >img[:,:,2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select

# Define a function to convert to rover-centric coordinates
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the 
    # center bottom of the image.  
    x_pixel = np.absolute(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[0]).astype(np.float)
    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle) 
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to apply a rotation to pixel positions
def rotate_pix(xpix, ypix, yaw):
    # Convert yaw to radians
    yaw_rad = yaw * np.pi / 180
    xpix_rotated = (xpix * np.cos(yaw_rad)) - (ypix * np.sin(yaw_rad))
                            
    ypix_rotated = (xpix * np.sin(yaw_rad)) + (ypix * np.cos(yaw_rad))
    # Return the result  
    return xpix_rotated, ypix_rotated

# Define a function to perform a translation
def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale): 
    # Apply a scaling and a translation
    xpix_translated = (xpix_rot / scale) + xpos
    ypix_translated = (ypix_rot / scale) + ypos
    # Return the result  
    return xpix_translated, ypix_translated

# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):
           
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image
    
    mask = cv2.warpPerspective(np.ones_like(img[:,:,0]), M, (img.shape[1], img.shape[0]))# keep same size as input image
    return warped,mask


# Apply the above functions in succession and update the Rover state accordingly
def perception_step(Rover):
    # Perform perception steps to update Rover()
    # TODO: 
    # NOTE: camera image is coming to you in Rover.img
    image=Rover.img
    #img=Rover.img
    # 1) Define source and destination points for perspective transform
    bottom_offset = 6
    dst_size = 5
    source = np.float32([[14, 140], [301 ,140],[200, 96], [118, 96]])
    destination = np.float32([[image.shape[1]/2 - dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - 2*dst_size - bottom_offset], 
                  [image.shape[1]/2 - dst_size, image.shape[0] - 2*dst_size - bottom_offset],
                  ])
    # 2) Apply perspective transform
    warped,mask = perspect_transform(Rover.img, source, destination)
    # 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
    threshed = color_thresh(warped)  
    threshed_rock = color_thresh_rock(warped)
    threshed_obj = color_thresh_obj(warped)
    obs_map =np.absolute(np.float32(threshed)-1)*mask
    #obs_map =threshed_obj*mask
    # 4) Convert thresholded image pixel values to rover-centric coords
    # 4) Update Rover.vision_image (this will be displayed on left side of screen)
    
        # Example: Rover.vision_image[:,:,0] = obstacle color-thresholded binary image
        #          Rover.vision_image[:,:,1] = rock_sample color-thresholded binary image
        #          Rover.vision_image[:,:,2] = navigable terrain color-thresholded binary image
    Rover.vision_image[:,:,0] =obs_map*255
    Rover.vision_image[:,:,1] =threshed_rock*255
    Rover.vision_image[:,:,2] =threshed*255
    # 5) Convert map image pixel values to rover-centric coords
    xpix, ypix = rover_coords(threshed) 
    # 6) Convert rover-centric pixel values to world coordinates
    scale = 10
    rover_yaw = Rover.yaw
    rover_xpos,rover_ypos = Rover.pos
    #rover_ypos = Rover.ypos
    navigable_x_world, navigable_y_world = pix_to_world(xpix, ypix, rover_xpos, 
                                rover_ypos, rover_yaw, 
                                Rover.worldmap.shape[0], scale)
    ##ROCK#####################################################
  
    #  Convert thresholded image pixel values to rover-centric coords
    #xpix_r, ypix_r = rover_coords(threshed_rock)
    # Generate 200 x 200 pixel worldmap
    #worldmap = np.zeros((200, 200))
    scale =10
    Rover.worldmap[navigable_y_world, navigable_x_world, 2] += 10
    # 8) Convert rover-centric pixel positions to polar coordinates
    rover_centric_pixel_distances, rover_centric_angles = to_polar_coords(xpix, ypix)
    #rover_rock_distances, rover_rock_angles = to_polar_coords(xpix_r, ypix_r)
    

    #mean_dir = np.mean(angles)
    # Update Rover pixel distances and angles
    Rover.nav_dists = rover_centric_pixel_distances 
    Rover.nav_angles = rover_centric_angles
    ##OBJ#######################################################
    #  Convert thresholded image pixel values to rover-centric coords
    threshed_obj= color_thresh_obj(warped) 
    # 4) Convert thresholded image pixel values to rover-centric coords
    xpix_o, ypix_o = rover_coords(threshed_obj)
    obx,oby=rover_coords(obs_map)
    scale = 10
    obstacle_x_world, obstacle_y_world= pix_to_world(obx, oby, rover_xpos, 
                                rover_ypos, rover_yaw, 
                                Rover.worldmap.shape[0], scale)
    ##############################################################
    # 7) Update worldmap (to be displayed on right side of screen)
        # Example: Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1
        #          Rover.worldmap[rock_y_world, rock_x_world, 1] += 1
        #          Rover.worldmap[navigable_y_world, navigable_x_world, 2] += 1
    Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1
    #nav_pix= Rover.worldmap[:,:,2] > 25
    #Rover.worldmap[nav_pix,0]=0
    if threshed_rock.any():
        xpix_r, ypix_r = rover_coords(threshed_rock)
        rover_rock_distances, rover_rock_angles = to_polar_coords(xpix_r, ypix_r)
        rock_x_world, rock_y_world, = pix_to_world(xpix_r, ypix_r, rover_xpos, 
                                rover_ypos, rover_yaw, 
                                Rover.worldmap.shape[0], scale)
        rock_idx=np.argmin(rover_rock_distances)
        rock_ycen,rock_xcen=rock_y_world[rock_idx], rock_x_world[rock_idx]
        Rover.worldmap[rock_ycen, rock_xcen, 1]=255
        Rover.vision_image[:,:,1]=threshed_rock*255
    else:
        Rover.vision_image[:,:,1]=0
    
    #Rover.rock_dists = rover_rock_distances
    #Rover.rock_angles = rover_rock_angles
 
    
    
    return Rover