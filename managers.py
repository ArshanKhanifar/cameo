import cv2
import numpy
import time

class CaptureManager(object):
    
    def __init__(self, capture, previewWindowManager = None, shouldMirrorPreview = False):
        
        self.previewWindowManager = previewWindowManager
        self.shouldMirrorPreview = shouldMirrorPreview

        self._capture = capture
        self._channel = 0
        self._enteredFrame = False
        self._frame = None
        self._imageFileName = None
        self._videoFileName = None
        self._videoEncoding = None
        self._videoWriter = None
        self._startTime = None
        self._framesElapsed = 0
        self._fpsEstimate = None

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, value):
        if self._channel != value:
            self._channel = value
            self._frame = None

    @property
    def frame(self):
        if self._enteredFrame and self._frame is None:
            _, self._frame = self._capture.retrieve()
            return self._frame

    @property
    def isWritingImage(self):
        
        return self._imageFileName is not None
    
    @property
    def isWritingVideo(self):

        return self._videoFileName is not None

    def enterFrame(self):
        """Capture the next frame, if any"""
        # But first, check that if any previous frame was exitted.
        assert not self._enteredFrame, 'previous enterFrame() had no matching exitFrame()'

        if self._capture is not None:
            self._enteredFrame = self._capture.grab()

    def exitFrame(self):
        """Draw to the window, write to files, exit the frame."""
        
        # Check whether any grabbed frame is retrievable.
        # The getter may retrieve and cache the frame.
        
        if self._frame is None:
            self._enteredFrame = False
            return
        
        # Update the FPS estimate and related variables. 

        if self._framesElapsed == 0:
            self._startTime = time.time()
        else:
            timeElapsed = time.time() - self._startTime
            self._fpsEstimate = self._framesElapsed / timeElapsed
            self._framesElapsed += 1

        # Draw to the window, if any.

        if self.previewWindowManager is not None:
            if self.shouldMirrorPreview:
                mirroredFrame = numpy.fliplr(self._frame).copy()
                self.previewWindowManager.show(mirroredFrame)
            else:
                self.previewWindowManager.show(self._frame)

        # Write to the image file, if any.

        if self.isWritingImage:
            cv2.imwrite(self._imageFileName, self._frame)
            self._imageFileName = None
            
        # Write to the video file, if any.

        self._writeVideoFrame()

        # Release the frame

        self._frame = None
        self._enteredFrame = None

    def writeImage(self, filename):
        """ Write the next exitted frame to an image file. """
        self._imageFileName = filename

    def startWritingVideo(self, filename, encoding = cv2.VideoWriter_fourcc('I', '4', '2', '0')):
        """ Start writing exitted frames to a video file. """
        self._videoFileName = filename
        self._videoEncoding = encoding
        self._videoWriter = None
    
    def stopWritingVideo(self):
        """ Stop writing exitted frames to a video file. """
        self._videoFileName = None
        self._videoEncoding = None
        self._videoWriter = None
    
    def _writeVideoFrame(self):
        if not self.isWritingVideo:
            return

        if self._videoWriter is None:
            fps = self._capture.get(cv2.CAP_PROP_FPS)
            if fps == 0.0:
                # The capture's fps is unknown so use an estimate
                
                if self._framesElapsed < 20:
                    # Wait till more frames are elapsed so esitmate is more stable
                    return
                else:
                    fps = self._fpsEstimate
    
            size = (int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            self._videoWriter = cv2.VideoWriter(self._videoFileName, self._videoEncoding, fps, size)
            
        self._videoWriter.write(self._frame)
    
                
class WindowManager(object):

    def __init__(self, windowName, keypressCallback = None):
        self.keypressCallback = keypressCallback

        self._windowName = windowName
        self._isWindowCreated = False

    @property
    def isWindowCreated(self):
        return self._isWindowCreated

    def createWindow(self):
        cv2.namedWindow(self._windowName)
        self._isWindowCreated = True
    
    def show(self, frame):
        cv2.imshow(self._windowName, frame)
    
    def destroyWindow(self):
        cv2.destroyWindow(self._windowName)
        self._isWindowCreated = False
    
    def processEvents(self):
        keycode = cv2.waitKey(1)
        if self.keypressCallback is not None and keycode != -1:
            # Discard and non-ASCII info encoded by GTK.
            keycode &= 0xFF
            self.keypressCallback(keycode)
    