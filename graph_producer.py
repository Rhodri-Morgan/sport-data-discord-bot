import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.gridspec as gridspec
import numpy as np
import math
import os


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
        self.large_font = fm.FontProperties(fname=os.path.join(os.getcwd(), 'sources', 'Whitney Medium.ttf'), size=16)
        self.medium_font = fm.FontProperties(fname=os.path.join(os.getcwd(), 'sources', 'Whitney Medium.ttf'), size=12)
        self.small_font = fm.FontProperties(fname=os.path.join(os.getcwd(), 'sources', 'Whitney Medium.ttf'), size=10)


    def preprocess_data(self, probabilities_dict):
        """ Prepares data for displaying in chart (combining values and ordering) """
        max_key = None
        removed_keys = []
        cumulative_values = 0.0
        for key, value in probabilities_dict.items():
            if max_key is None or len(key) > len(max_key):
                max_key = key
            if value < 1.0:
                removed_keys.append(key)
                cumulative_values += value

        if cumulative_values != 0.0:
            [probabilities_dict.pop(key) for key in removed_keys]
            probabilities_dict['Cumulative Other (< 1%)'] = cumulative_values
            if len(max_key) < len('Cumulative Other (< 1%)'):
                max_key = 'Cumulative Other (< 1%)'
        return max_key, probabilities_dict


    def barplot(self, event_name, market_name, datetime, probabilities_dict):
        """ Displays data in barchart form returning reference to chart """
        max_key, probabilities_dict = self.preprocess_data(probabilities_dict)

        barplot_colours = []
        for value in probabilities_dict.values():
            barplot_colours.append(self.colours[math.ceil(value)-1])

        width = 8.4 if len(probabilities_dict)/0.476 < 8.4 else len(probabilities_dict)/0.476
        height = 8.4 if len(max_key)/3.09 < 8.4 else len(max_key)/3.09
        height += 5

        fig, ax = plt.subplots(figsize=(width, height))
        gs = gridspec.GridSpec(2, 1, width_ratios=[1], height_ratios=[height,height/20])
        fig.clf()
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])

        ax1.patch.set_facecolor('#36393f')
        ax2.patch.set_facecolor('#36393f')

        plt.sca(ax1)
        plt.bar(probabilities_dict.keys(), probabilities_dict.values(), align='center', color=barplot_colours)
        plt.xticks(rotation=90, color='white', fontproperties=self.medium_font)
        plt.xlabel('\n' + event_name + ' Runners\n\n', color='white', fontproperties=self.large_font)
        plt.yticks(np.arange(0, 101, step=5), fontsize=8, color='white', fontproperties=self.medium_font)
        plt.ylabel(market_name + ' (%)', color='white', fontproperties=self.large_font)
        plt.text(0.99, 0.99, 'Source - Betfair.com API\nDate Processed (UTC) - {0}'.format(datetime),
                fontproperties=self.small_font,
                color='white',
                horizontalalignment='right',
                verticalalignment='top',
                transform=ax1.transAxes)
        plt.tight_layout()

        plt.sca(ax2)
        plt.bar([x for x in range(100)], [100 for x in range(100)], align='center', width=1.0, color=self.colours)
        plt.box(False)
        x_ticks = ['' for x in range(100)]
        x_ticks[0] = '0%'
        x_ticks[49] = '50%'
        x_ticks[99] = '100%'
        plt.tick_params(length=0)
        plt.xticks(np.arange(100), x_ticks, color='white', fontproperties=self.small_font)
        plt.yticks([])
        plt.tight_layout()

        return fig


    def piechart(self, event_name, market_name, datetime, probabilities_dict):
        """ Displays data in piechart form returning reference to chart """
        max_key, probabilities_dict = self.preprocess_data(probabilities_dict)
        if sum(probabilities_dict.values()) < 90:
            return None

        fig, ax = plt.subplots(figsize=(12.8, 12.8))
        fig.clf()

        explode = [0.0 for x in probabilities_dict.values()]
        explode[0] = 0.1
        plt.pie(probabilities_dict.values(), labels=probabilities_dict.keys(), shadow=True, explode=explode,
                textprops={'fontproperties': self.medium_font, 'color': 'white'})
        plt.title('{0}\n{1}'.format(event_name, market_name), color='white', fontproperties=self.large_font)
        return plt
