import json
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.image as image
from tempfile import NamedTemporaryFile
import urllib
from urllib.request import urlopen
import matplotlib.font_manager as fm

class graphing_func:
    def __init__(self):
        with open(os.path.join(os.getcwd(), 'driver_colour_directory.json')) as f:
            self.driver_colour_directory_data = json.load(f)

    def dataset_instances_dates_list(self, json_data):
        dates=[]
        for key1 in json_data.keys():
            dates.append(key1)
        return dates


    def merged_dictionary(self, json_data):
        merged_dictionary={}
        for value1 in json_data.values():
            for key2,value2 in value1.items():
                if key2 in merged_dictionary:
                    merged_dictionary[key2].append(np.nan_to_num(value2))
                else:
                    merged_dictionary[key2] = [np.nan_to_num(value2)]
        return merged_dictionary


    def driver_colors_matcher_loop(self, merged_dictionary):
        colors_lst=[]
        for key1 in merged_dictionary.keys():
            for key2,value2 in self.driver_colour_directory_data.items():
                if key1==key2:
                    colors_lst.append(value2)
        return colors_lst


    def most_recent_dataset_dictionary_for_pie(self, json_data):
        key1,value1 = max(json_data.items())
        latest_dict=value1
        zerod_dict={}
        for key2,value2 in latest_dict.items():
            zerod_dict[key2] = [np.nan_to_num(value2)]
        return zerod_dict

    def most_recent_dataset_dictionary_for_bar(self, json_data):
        key1,value1 = max(json_data.items())
        latest_dict=value1
        zerod_dict={}
        for key2,value2 in latest_dict.items():
            if value2>5:
                zerod_dict[key2] = np.nan_to_num(value2)
        return zerod_dict

    def convert_dictionary_to_list(self, dictionary):
        lst=[]
        for key, value in dictionary.items():
            lst.append(key + ' ' + '(' + str(value[-1]) + '%' + ')')
        return lst

    def stackplot(self, json_data, title, xlabel, ylabel):
        fig, ax=plt.subplots()
        plt.stackplot(self.dataset_instances_dates_list(json_data), 
                    self.merged_dictionary(json_data).values(), 
                    labels=self.convert_dictionary_to_list(self.merged_dictionary(json_data)), 
                    colors=self.driver_colors_matcher_loop(self.merged_dictionary(json_data)), 
                    alpha=1)
        
        ax.set_facecolor('#ffffff')
        fig.set_facecolor('#ffffff')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.xaxis.set_ticks_position('none') 
        ax.yaxis.set_ticks_position('none') 
        plt.margins(0, 0, tight=True)
        plt.subplots_adjust(left=0.07, bottom=0.08, right=0.87, top=0.94, wspace=0.2, hspace=0.2)
        
        github_url = 'https://github.com/google/fonts/blob/master/ofl/titilliumweb/TitilliumWeb-Regular.ttf'
        url = github_url + '?raw=true'
        response = urlopen(url)
        f = NamedTemporaryFile(delete=False, suffix='.ttf')
        f.write(response.read())
        f.close()
        prop = fm.FontProperties(fname=f.name, size=15)

        plt.yticks([10,20,30,40,50,60,70,80,90,100], fontproperties=prop, size=15)
        plt.xticks(fontproperties=prop, size=15)
        plt.title(title, fontproperties=prop, size=30, loc='Center', pad=20)
        plt.xlabel(xlabel, fontproperties=prop, size=20)
        plt.ylabel(ylabel, fontproperties=prop, size=20)
        plt.legend(bbox_to_anchor=(1.15, 0.75), loc='upper right', fancybox=True, frameon=False, prop=prop)

        plt.show()

    def piechart(self, json_data, title):
        sizes = self.most_recent_dataset_dictionary_for_pie(json_data).values()
        labels = self.convert_dictionary_to_list(self.most_recent_dataset_dictionary_for_pie(json_data))
        fig1, ax1 = plt.subplots()
        ax1.pie(sizes,
                shadow=False, 
                colors=self.driver_colors_matcher_loop(self.merged_dictionary(json_data)), 
                startangle=90)

        github_url = 'https://github.com/google/fonts/blob/master/ofl/titilliumweb/TitilliumWeb-Regular.ttf'
        url = github_url + '?raw=true'
        response = urlopen(url)
        f = NamedTemporaryFile(delete=False, suffix='.ttf')
        f.write(response.read())
        f.close()
        prop = fm.FontProperties(fname=f.name, size=15)

        plt.title(title, fontproperties=prop, size=30)
        ax1.legend(labels, loc="center right", fancybox=True, frameon=False, prop=prop)
        ax1.axis('equal')

        plt.show()

    def barchart(self, json_data, title, xlabel, ylabel):
        fig, ax=plt.subplots()
        x = self.most_recent_dataset_dictionary_for_bar(json_data).keys()
        y = self.most_recent_dataset_dictionary_for_bar(json_data).values()
        plt.bar(x, y, color=self.driver_colors_matcher_loop(self.merged_dictionary(json_data)))

        ax.set_facecolor('#ffffff')
        fig.set_facecolor('#ffffff')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.xaxis.set_ticks_position('none') 
        ax.yaxis.set_ticks_position('none') 
        plt.margins(0, 0, tight=True)

        github_url = 'https://github.com/google/fonts/blob/master/ofl/titilliumweb/TitilliumWeb-Regular.ttf'
        url = github_url + '?raw=true'
        response = urlopen(url)
        f = NamedTemporaryFile(delete=False, suffix='.ttf')
        f.write(response.read())
        f.close()
        prop = fm.FontProperties(fname=f.name, size=15)

        plt.xlabel(xlabel, fontproperties=prop, size=20)
        plt.ylabel(ylabel, fontproperties=prop, size=20)
        plt.title(title, fontproperties=prop, size=30, loc='Center', pad=20)

        plt.show()
