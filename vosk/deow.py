# from sketchpy import canvas
#
# obj = canvas.sketch_from_image('')
# obj.draw()
from sketchpy import canvas
from sketchpy.canvas import sketch_from_svg

object: sketch_from_svg = canvas.sketch_from_svg('D:\jarvisAI\vosk\vosk-model-small-hi-0.22\man.svg')
object.draw()
