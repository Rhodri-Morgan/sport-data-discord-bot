import matplotlib.pyplot as plt
import numpy as np
import math


class GraphProducer:
    def __init__(self):
        # Colour gradient ranging from red to blue
        self.colours = ['#0400ff', '#0600fc', '#0900f9', '#0b00f7', '#0e00f4', '#1000f2', '#1300ef', '#1500ec', '#1800ea', '#1a00e7', 
                        '#1d00e5', '#1f00e2', '#2200e0', '#2400dd', '#2700da', '#2a00d8', '#2c00d5', '#2f00d3', '#3100d0', '#3400ce', 
                        '#3600cb', '#3900c8', '#3b00c6', '#3e00c3', '#4000c1', '#4300be', '#4500bc', '#4800b9', '#4a00b6', '#4d00b4', 
                        '#5000b1', '#5200af', '#5500ac', '#5700aa', '#5a00a7', '#5c00a4', '#5f00a2', '#61009f', '#64009d', '#66009a', 
                        '#690097', '#6b0095', '#6e0092', '#710090', '#73008d', '#76008b', '#780088', '#7b0085', '#7d0083', '#800080', 
                        '#82007e', '#85007b', '#870079', '#8a0076', '#8c0073', '#8f0071', '#91006e', '#94006c', '#970069', '#990067', 
                        '#9c0064', '#9e0061', '#a1005f', '#a3005c', '#a6005a', '#a80057', '#ab0054', '#ad0052', '#b0004f', '#b2004d', 
                        '#b5004a', '#b80048', '#ba0045', '#bd0042', '#bf0040', '#c2003d', '#c4003b', '#c70038', '#c90036', '#cc0033', 
                        '#ce0030', '#d1002e', '#d3002b', '#d60029', '#d80026', '#db0024', '#de0021', '#e0001e', '#e3001c', '#e50019', 
                        '#e80017', '#ea0014', '#ed0012', '#ef000f', '#f2000c', '#f4000a', '#f70007', '#f90005', '#fc0002', '#ff0000']

    def barplot(self, event_name, market_name, datetime, probabilities_dict):
        barplot_colours = []
        for value in probabilities_dict.values():
            barplot_colours.append(self.colours[math.ceil(value)-1])

        fig, ax = plt.subplots()
        plt.bar(probabilities_dict.keys(), probabilities_dict.values(), align='center', color=barplot_colours)
        plt.title(event_name + ' - ' + market_name)
        plt.xticks(rotation=90, fontsize=8)
        plt.xlabel(event_name + ' runners')
        plt.yticks(np.arange(0, 101, step=5), fontsize=8)
        plt.ylabel(market_name + ' %')
        ax.text(0.99, 0.99, 'Source - Betfair.com API\nDate Processed (UTC) - {0}'.format(datetime), fontsize=6,
                horizontalalignment='right',
                verticalalignment='top',
                transform=ax.transAxes)
        plt.tight_layout()
        return plt
        