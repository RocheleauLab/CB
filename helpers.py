def calc_kfactors(numaper):
    indexofref = 1.518
    theta = math.asin(numaper/indexofref)
    costheta = math.cos(theta)
    kdenom = 1-costheta

    ka = (2 - (3*costheta) + (math.pow(costheta, 3))) / (6*kdenom)
    kb = (1 - (3*costheta) + (3*(math.pow(costheta, 2))) - (math.pow(costheta,3))) / (24*kdenom)
    kc = (5 - (3*costheta) - (math.pow(costheta,2)) - (math.pow(costheta,3))) / (8*kdenom)
    
    return ka, kb, kc


def medfilt(image):
    circ_rad2 = np.asarray([[0,1,1,1,0],[1,1,1,1,1],[1,1,1,1,1],[1,1,1,1,1],[0,1,1,1,0]])
    filt_image = ndimage.median_filter(image, footprint=circ_rad2, mode='nearest')
    return filt_image


def bandpass(image):
    # Threshold upper & lower 5% of intensity
    lower=200
    upper=3900
        
    image[image<lower]=0
    image[image>upper]=0
    return image


def preprocess(imageset, bgroizippath, gfactor, numaper):
    ka, kb, kc = calc_kfactors(numaper)
    raw_perp = imageset[0]
    raw_para = imageset[1]
    
    mask = np.ones_like(raw_perp)
    bgroi = read_roi.read_roi_zip(bgroizippath)
    
    for k,l in bgroi.items():
        y1, y2, x1, x2 = int(l['top']), int(l['top']+l['height']), int(l['left']), int(l['left']+l['width'])
        perp_bgroi = raw_perp[y1:y2, x1:x2]
        perp_bg = perp_bgroi[np.nonzero(perp_bgroi)].mean()
        para_bgroi = raw_para[y1:y2, x1:x2]
        para_bg = para_bgroi[np.nonzero(para_bgroi)].mean()
    
    # Subtract background, apply {median filter, thresholding, masking}
    sub_perp = raw_perp - perp_bg
    final_perp = bandpass(medfilt(sub_perp))
    sub_para = raw_para - para_bg
    final_para = bandpass(medfilt(sub_para))    
    mask[final_perp==0]=0
    mask[final_para==0]=0
    
    # Generate anisotropy image
    aniso_num = (final_para*(ka+kb+kc))-(final_perp*gfactor*(ka+kb+kc))
    aniso_denom = (final_para*(ka-(2*kb)+kc))+(final_perp*gfactor*((2*kc)-ka-kb))
    aniso = np.divide(aniso_num, aniso_denom, out=np.zeros_like(aniso_num), where=(aniso_denom!=0))
    
    # Mask anisotropy image
    aniso[mask==0]=0
    final_para[mask==0]=0
    final_perp[mask==0]=0
    
    return final_perp, final_para, aniso


def evalroi(perp, para, aniso, fullimage):
    infos=[]
    
    if (perp.sum()==0 or para.sum()==0 or aniso.sum()==0):
            return infos
    else:
            pixused = np.count_nonzero(aniso)
            pixfraction = pixused/aniso.size
            
            avganiso = aniso[np.nonzero(aniso)].mean()
            stdev = aniso[np.nonzero(aniso)].std()
            stderr = stdev/math.sqrt(pixused)

            avgperp = perp[np.nonzero(perp)].mean()
            avgpara = para[np.nonzero(para)].mean()
            minperp = perp[np.nonzero(perp)].min()
            maxpara = para[np.nonzero(para)].max()
            
            if fullimage==False:
                if pixfraction<0.8:
                    return ['',avganiso, pixused, pixfraction, avgperp, avgpara, minperp, maxpara]
                
            if fullimage==True:
                if pixused<1000:
                    return ['',avganiso, pixused, pixfraction, avgperp, avgpara, minperp, maxpara]

            infos = [avganiso, stderr, pixused, pixfraction, avgperp, avgpara, minperp, maxpara]
    return infos


def applyxroi(y1, y2, x1, x2, perp, para, aniso):
    perp[y1:y2, x1:x2] = 0
    para[y1:y2, x1:x2] = 0
    aniso[y1:y2, x1:x2] = 0
    return perp, para, aniso


def ana_aniso(mainfolderpath, folderlist, resultsfilename, gfactor, numaper):
    print('Now analyzing '+mainfolderpath+" !")
    for subfolder in folderlist:
        datafolderpath = os.path.join(mainfolderpath, subfolder)
        filelist = os.listdir(datafolderpath)
        print('Starting '+subfolder+'!')

        with open(resultsfilename, mode='a') as csvFile:
            writer = csv.writer(csvFile, lineterminator='\n')
            writer.writerow([datafolderpath])
            writer.writerow(['Image','Avg Aniso', 'Std Error', 'Pixels Used', '% Pixels Used', \
                             'Avg Perp', 'Avg Para', 'Min Perp', 'Max Para', 'ROI #', 'GFactor', 'NA'])

            for i in range(len(filelist)):
                filepath = os.path.join(datafolderpath, filelist[i])

                # Open .lsm files
                if (filepath.endswith('.lsm')): 
                    print('Working on '+filelist[i]+'...')
                    rawimage = tf.imread(filepath)
                    numslices = rawimage.shape[1]
                    imagestack = np.zeros((numslices, 2, rawimage.shape[3], rawimage.shape[4])) 

                    xroizippath = filepath[:-4]+ '--xROI.zip'
                    for slice in range(numslices):
                        imagestack[slice] = rawimage[0][slice][:2]
                        perp, para, aniso = preprocess(imagestack[slice], filepath[:-4] + '--BGROI.zip', \
                                                       gfactor, numaper)

                        # Clear debris                    
                        if (os.path.exists(xroizippath)):
                            xrois = read_roi.read_roi_zip(xroizippath)
                            for k,l in xrois.items():
                                y1, y2, x1, x2 = l['top'], l['top']+l['height'], l['left'], l['left']+l['width']
                                perp, para, aniso = applyxroi(y1, y2, x1, x2, perp, para, aniso)

                        # ROIs exist
                        roizippath = filepath[:-4]+ '--ROI.zip'
                        if(os.path.exists(roizippath)):            
                            rois = read_roi.read_roi_zip(roizippath)
                                
                            n = 1
                            for k,l in rois.items():
                                y1, y2, x1, x2 = l['top'], l['top']+l['height'], l['left'], l['left']+l['width']
                                perp_roi = perp[y1:y2, x1:x2]
                                para_roi = para[y1:y2, x1:x2]
                                aniso_roi = aniso[y1:y2, x1:x2]

                                if numslices==1:
                                    infos = evalroi(perp_roi, para_roi, aniso_roi, False)
                                    if(infos==[]):
                                        writer.writerow([filelist[i]])
                                    else:
                                        writer.writerow([filelist[i]]+infos+[n, gfactor, numaper])
                                    n = n + 1
                                else:
                                    infos=evalroi(perp_roi, para_roi, aniso_roi, True)
                                    if(infos==[]):
                                        writer.writerow([filelist[i]])
                                    else:
                                        writer.writerow([filelist[i]]+infos+[slice, gfactor, numaper])
                                
                        # No ROIs
                        else:
                            infos=evalroi(perp, para, aniso, True)
                            if(infos==[]):
                                writer.writerow([filelist[i]])
                            else:
                                writer.writerow([filelist[i]]+infos+[slice, gfactor, numaper])

        csvFile.close()
        print('Done with '+subfolder+'!')
    print('Done with all the folders!')
    

def importtest(test):
    print("Hello "+test+"!")