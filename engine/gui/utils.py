import os
from panda3d.core import TextPropertiesManager, TextProperties


def hex_to_rgb(str_hex, alpha=1.0):
    """
    Map an hex string to a RGB color

    Args:
        str_hex (str): the string that should begin with *#*
        alpha (:obj:`float`, optional): the alpha channel (should be between 0.0 and 1.0)

    Returns:
        a :obj:`tuple` with :code:`(r, g, b, a)`
    """
    to_list = [int(str_hex.replace('#', "").strip()[i:i + 2], 16) for i in (0, 2, 4)]
    return to_list[0] / 255, to_list[1] / 255, to_list[2] / 255, alpha


def build_text_properties(engine):
    """
    Build the common text properties (font, color etc)

    Args:
        engine: the main engine
    """
    from engine.gui.gui import Gui

    # text properties
    props = TextPropertiesManager.getGlobalPtr()

    tp = TextProperties()
    tp.setSlant(.2)
    # set default text font
    tp.set_default_font(engine.loader.load_font(os.path.join(engine("font_path"), engine('font'))))
    props.setProperties('italic', tp)

    tp = TextProperties()
    tp.setSlant(.3)
    # set default text font
    tp.set_default_font(engine.loader.load_font(os.path.join(engine("font_path"), engine('font'))))
    tp.set_text_color(Gui.colors['red'])
    props.setProperties('warning', tp)

    tp = TextProperties()
    tp.setSlant(.2)
    tp.set_text_color(Gui.colors['golden'])
    tp.set_default_font(engine.loader.load_font(os.path.join(engine("font_path"), engine('font'))))
    props.setProperties('chrono', tp)

    tp = TextProperties()
    tp.setSlant(.2)
    tp.set_text_color(Gui.colors['red'])
    tp.set_default_font(engine.loader.load_font(os.path.join(engine("font_path"), engine('font'))))
    props.setProperties('chrono-alert', tp)

    tp = TextProperties()
    tp.set_font(engine.loader.load_font(os.path.join(engine("font_path"), engine('font_bold'))))
    props.setProperties('bold', tp)

    tp = TextProperties()
    tp.setSlant(.2)
    tp.set_text_color((1.0, 1.0, 1.0, 0.2))
    props.setProperties('hint', tp)

    tp = TextProperties()
    # tp.setSlant(.2)
    # tp.set_text_scale(1.1)
    tp.set_text_color((0.2, 0.8, 0.5, 1.0))
    # tp.set_font(engine.loader.load_font(os.path.join(engine("font_path"), 'UbuntuMono-B.ttf')))
    props.setProperties('terminal', tp)

    tp = TextProperties()
    tp.set_text_scale(1.2)
    tp.set_text_color(Gui.colors['golden'])
    tp.set_font(engine.loader.load_font(os.path.join(engine("font_path"),
                                                     engine('font_bold'))))
    props.setProperties('title', tp)

    # colors as properties
    for k in Gui.colors:
        tp = TextProperties()
        tp.set_text_color(Gui.colors[k])
        # tp.set_font(engine.loader.load_font(os.path.join(engine("font_path"),
        #                                                  engine('font'))))
        props.setProperties(k, tp)
