# Mock version of st7735 display

BG_SPI_CS_FRONT="front"

class ST7735:
    def __init__(self, port, cs, dc, backlight, rotation, spi_speed_hz):
        pass

    def begin(self):
        pass

    def display(self, image):
        pass
