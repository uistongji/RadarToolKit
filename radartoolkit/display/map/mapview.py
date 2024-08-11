#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# This code is part of package RadarToolKit (RTK).
# 
# RadarToolKit (RTK) manages the track, view, processing, analysis and simulation of radargrams, 
# e.g., impulse and chirp. The distributed version focuses on the chirped system utilized in Antarctica,
# namely the ice sounding radar (ISR). Therefore RTK currently is also called as RadarToolKit (ISR).
#
# RTK is distributed in the hope that it would be helpful for
# the users that needs to generate paper-like image results,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# You should have received a copy of the GNU General Public License
# together with the RadarToolKit (ISR): https://github.com/uistongji/RadarToolKit
#
# AUTHOR: Jiaying Zhou (supervisor: Tong Hao), Tongji University


""" this file contains the drawing methods
"""


import os
import time
import math
import rasterio
import numpy as np
import geopandas as gpd
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.collections as mc
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from scipy.spatial import KDTree
from shapely import LineString, MultiLineString, GeometryCollection

from ..bindings import (QtGui, QtCore, Qt, QThread, Signal, QObject, 
                        QtSlot,QApplication, QVBoxLayout, QPushButton, 
                        QWidget, QHBoxLayout, QGridLayout, QMessageBox)

from display.settings import ICONS_DIR



class GeoTIFFLoader(QObject):

    data_loaded = Signal(np.ndarray, tuple)

    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath
        self.dataset = None
        self.transform = None


    def load_geotiff(self):
        with rasterio.open(self.filepath) as src:
            self.dataset = src.read(1)
            self.transform = src.transform


    @QtSlot(float, float, float, float)
    def load_data_for_bounds(self, x0, y0, x1, y1):
        if self.dataset is None:
            return
        window = rasterio.windows.from_bounds(x0, y0, x1, y1, self.transform)
        row_start, row_stop = int(window.row_off), int(window.row_off + window.height)
        col_start, col_stop = int(window.col_off), int(window.col_off + window.width)
        data = self.dataset[row_start:row_stop, col_start:col_stop]
        extent = (x0, x1, y0, y1)
        self.data_loaded.emit(data, extent)



class MapView(QWidget):

    recordSelected = QtCore.Signal(int)

    def __init__(self):
        super().__init__()
        self.colors = ['blue', 'green', 'pink', 'orange', 'brown']
        self.recordcount = 0
        self.colori = 0
        self.legend_handles = []
        self.others_legend_added = False
        self.line_objects = {}
        self.last_check = 0
        self.current_highlighted_line = None 
        self.orig_xlim = None
        self.orig_ylim = None
        self.is_panning = False
        self.ctrl_pressed = False
        self.current_x = None
        self.current_y = None
        self.global_rect = None
        self.kdtrees = []
        self.geotiff_loader = GeoTIFFLoader('radartoolkit/display/resources/map/00000-20080319-092059124.tif')
        self.geotiff_thread = QThread()
        self.geotiff_loader.moveToThread(self.geotiff_thread)
        self.geotiff_loader.data_loaded.connect(self.on_geotiff_loaded)
        self.geotiff_thread.started.connect(self.geotiff_loader.load_geotiff)
        self.geotiff_thread.start()
        self.drawn_paths = set()
        self.initUI()


    def maintain_aspect_ratio(self, ax, aspect_ratio=3/2):
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        current_ratio = abs((x1 - x0) / (y1 - y0))
        center_x, center_y = (x0 + x1) / 2, (y0 + y1) / 2
        if current_ratio > aspect_ratio:
            new_height = (x1 - x0) / aspect_ratio
            ax.set_ylim(center_y - new_height / 2, center_y + new_height / 2)
        else:
            new_width = (y1 - y0) * aspect_ratio
            ax.set_xlim(center_x - new_width / 2, center_x + new_width / 2)
        self.update_map_data()


    def update_map_data(self, geotiff=True):
        xlim = self.ax_zoomed.get_xlim()
        ylim = self.ax_zoomed.get_ylim()
        x_range = xlim[1] - xlim[0]
        y_range = ylim[1] - ylim[0]
        
        # Define a threshold for when to switch between GeoTIFF and shapefile
        threshold = (self.ax_global.dataLim.xmax - self.ax_global.dataLim.xmin) / 2

        if x_range < threshold and y_range < threshold and geotiff:
            self.clear_geotiff() # clear old
            self.geotiff_loader.load_data_for_bounds(xlim[0], ylim[0], xlim[1], ylim[1]) # load new
        else:
            self.clear_geotiff()
            self.ax_zoomed.set_xlim(xlim)
            self.ax_zoomed.set_ylim(ylim)
            self.fig_zoomed.canvas.draw_idle()


    def clear_geotiff(self):
        for artist in self.ax_zoomed.get_images():
            artist.remove()


    def on_geotiff_loaded(self, data, extent):
        cmap = plt.cm.gray
        cmap_list = cmap(np.arange(cmap.N))
        cmap_list[0] = [1, 1, 1, 1]
        custom_cmap = ListedColormap(cmap_list)
        self.ax_zoomed.imshow(data, cmap=custom_cmap, extent=extent, zorder=2)
        self.fig_zoomed.canvas.draw_idle()


    def initUI(self):
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(254, 254, 254))
        self.setPalette(p)

        layout = QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        # Load the shapefile using Geopandas
        world_shp = gpd.read_file('radartoolkit/display/resources/map/Coastline_Antarctica_v02.shp')
        projection = ccrs.Stereographic(central_longitude=0, central_latitude=-90)

        # Create the zoomed figure and axis
        self.fig_zoomed, self.ax_zoomed = plt.subplots(figsize=(1, 1), subplot_kw={'projection': projection})
        world_shp.plot(ax=self.ax_zoomed, color='lightgray', transform=projection, zorder=1)
        gridliner_zoomed = self.ax_zoomed.gridlines(draw_labels=True, linestyle='-.')
        gridliner_zoomed.xlocator = plt.FixedLocator(range(-180, 181, 30))
        gridliner_zoomed.ylocator = plt.FixedLocator(range(-90, -65, 5))
        self.ax_zoomed.axis("off")

        # Create the global figure and axis
        self.fig_global, self.ax_global = plt.subplots(figsize=(1, 1), subplot_kw={'projection': projection})
        world_shp.plot(ax=self.ax_global, color='lightgray', transform=projection)
        self.ax_global.axis("off")

        # Embed the plots in the Qt application
        self.canvas_zoomed = FigureCanvas(self.fig_zoomed)
        self.canvas_global = FigureCanvas(self.fig_global)

        self.canvas_zoomed.mpl_connect('scroll_event', self.on_scroll)
        self.canvas_zoomed.mpl_connect('button_press_event', self.on_click)
        self.canvas_zoomed.mpl_connect('button_release_event', self.on_release)
        self.canvas_zoomed.mpl_connect('motion_notify_event', self.on_mouse_move)

        # Add the zoomed map and global map to a grid layout
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.canvas_zoomed, 0, 0, 1, 1)
        grid_layout.addWidget(self.canvas_global, 0, 0, Qt.AlignTop | Qt.AlignRight)
        layout.addLayout(grid_layout)

        # Button to reset view
        h_layout2 = QHBoxLayout()
        btn_reset = QPushButton(QtGui.QIcon(os.path.join(ICONS_DIR, "full-view.png")), "")
        btn_reset.setIconSize(QtCore.QSize(24, 24))
        btn_reset.setFlat(True)
        btn_reset.setToolTip('Click to reset the view to its default state')
        h_layout2.addWidget(btn_reset)
        btn_reset.clicked.connect(self.reset_view)
        h_layout2.addStretch(1)

        layout.addLayout(h_layout2)

        self.setLayout(layout)

        # To track the mouse click and release for zoom box
        self.pressed = False
        self.x0 = None
        self.y0 = None
        self.rect = None


    def extract_coordinates(self, gdf):
        x_coords = []
        y_coords = []
        for geom in gdf.geometry:
            if geom is None:
                continue
            if isinstance(geom, LineString):
                xs, ys = geom.xy
                x_coords.extend(xs)
                y_coords.extend(ys)
            elif isinstance(geom, (MultiLineString, GeometryCollection)):
                for part in geom:
                    xs, ys = part.xy
                    x_coords.extend(xs)
                    y_coords.extend(ys)
            else:
                xs, ys = geom.xy
                x_coords.extend(xs)
                y_coords.extend(ys)
        return x_coords, y_coords


    def draw(self, ids, paths, projects, progress_dialog=None):
        # Initialize min and max values for x and y
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')

        # Determine the current zoom level and adjust line thickness accordingly
        line_thickness_zoomed = self.calculate_line_thickness(self.ax_zoomed)

        for index, (id, path, project) in enumerate(zip(ids, paths, projects)):
            # Check if the path exists
            if not os.path.exists(path):
                message_box = QMessageBox(self)
                message_box.setIcon(QMessageBox.Warning)
                message_box.setWindowTitle("File Not Found")
                message_box.setText(f"The file at path '{path}' does not exist. Please download the corresponding file or specify a different path.")
                message_box.setStandardButtons(QMessageBox.Ok)
                message_box.exec_()
                continue  # Skip this path and move to the next one

            if progress_dialog:
                progress_dialog.setValue(index)
                if progress_dialog.wasCanceled():
                    break

            if path in self.drawn_paths:
                if len(ids) == 1:
                    self.highlight_line(id)
                continue

            more_than_five = self.recordcount > 4
            global_lines = []
            zoomed_lines = []

            if os.path.isdir(path):
                folder_paths = [os.path.join(path, file) for file in os.listdir(path) if file.endswith('.shp')]
                for file_path in folder_paths:
                    gdf = gpd.read_file(file_path)
                    if not gdf.empty:
                        color = 'gray' if more_than_five else self.colors[self.colori % len(self.colors)]
                        label = 'Others' if more_than_five else f'{project}'

                        for geometry in gdf.geometry:
                            x, y = geometry.xy
                            global_lines.append(list(zip(x, y)))
                            zoomed_lines.append(list(zip(x, y)))
                            bounds = geometry.bounds
                            min_x = min(min_x, bounds[0])
                            max_x = max(max_x, bounds[2])
                            min_y = min(min_y, bounds[1])
                            max_y = max(max_y, bounds[3])

                        if not more_than_five:
                            self.legend_handles.append(mlines.Line2D([], [], color=color, label=label))
                        elif not self.others_legend_added:
                            self.legend_handles.append(mlines.Line2D([], [], color='gray', label='Others'))
                            self.others_legend_added = True

                        x, y = self.extract_coordinates(gdf)
                        self.kdtrees.append((id, KDTree(np.vstack((x, y)).T), color, line_thickness_zoomed))

                line_global = mc.LineCollection(global_lines, colors=color, linewidths=0.5, zorder=3)
                line_zoomed = mc.LineCollection(zoomed_lines, colors=color, linewidths=line_thickness_zoomed, zorder=3)
                self.ax_global.add_collection(line_global)
                self.ax_zoomed.add_collection(line_zoomed)
                self.line_objects[id] = (line_global, line_zoomed)
                self.drawn_paths.add(path)
                self.recordcount += 1
                self.colori += 1

            else:
                gdf = gpd.read_file(path)
                num_geometries = len(gdf.geometry)
                if not gdf.empty:
                    if len(paths) == 1 and progress_dialog:
                        progress_dialog.setMaximum(num_geometries)

                    color = 'gray' if more_than_five else self.colors[self.colori % len(self.colors)]
                    label = 'Others' if more_than_five else f'{project}'

                    for geom_index, geometry in enumerate(gdf.geometry):
                        if geometry is None:
                            continue
                        x, y = geometry.xy
                        global_lines.append(list(zip(x, y)))
                        zoomed_lines.append(list(zip(x, y)))

                        bounds = geometry.bounds
                        min_x = min(min_x, bounds[0])
                        max_x = max(max_x, bounds[2])
                        min_y = min(min_y, bounds[1])
                        max_y = max(max_y, bounds[3])

                        if len(paths) == 1 and progress_dialog:
                            progress_dialog.setValue(geom_index + 1)
                            if progress_dialog.wasCanceled():
                                break

                    if not more_than_five:
                        self.legend_handles.append(mlines.Line2D([], [], color=color, label=label))
                    elif not self.others_legend_added:
                        self.legend_handles.append(mlines.Line2D([], [], color='gray', label='Others'))
                        self.others_legend_added = True

                    x, y = self.extract_coordinates(gdf)
                    self.kdtrees.append((id, KDTree(np.vstack((x, y)).T), color, line_thickness_zoomed))

                line_global = mc.LineCollection(global_lines, colors=color, linewidths=0.5, zorder=3)
                line_zoomed = mc.LineCollection(zoomed_lines, colors=color, linewidths=line_thickness_zoomed, zorder=3)
                self.ax_global.add_collection(line_global)
                self.ax_zoomed.add_collection(line_zoomed)
                self.line_objects[id] = (line_global, line_zoomed)
                self.drawn_paths.add(path)
                self.recordcount += 1
                self.colori += 1

        if progress_dialog:
            progress_dialog.setValue(progress_dialog.maximum())

        dx = abs(max_x - min_x)
        dy = abs(max_y - min_y)
        buffer_x = dx * 0.1  # Adding a 10% buffer
        buffer_y = dy * 0.1
        if buffer_x > 0 and buffer_y > 0 and not (math.isinf(buffer_x) or math.isinf(buffer_y)):
            self.ax_zoomed.set_xlim(min_x - buffer_x, max_x + buffer_x)
            self.ax_zoomed.set_ylim(min_y - buffer_y, max_y + buffer_y)
            self.maintain_aspect_ratio(self.ax_zoomed)

        self.ax_zoomed.legend(handles=self.legend_handles, loc='lower right')

        xlim_zoomed = self.ax_zoomed.get_xlim()
        ylim_zoomed = self.ax_zoomed.get_ylim()
        xlim_global = self.ax_global.get_xlim()
        ylim_global = self.ax_global.get_ylim()
        x_threshold = xlim_global[1] - xlim_global[0]
        y_threshold = ylim_global[1] - ylim_global[0]

        if (xlim_zoomed[1] - xlim_zoomed[0] > x_threshold) or (ylim_zoomed[1] - ylim_zoomed[0] > y_threshold):
            self.update_map_data(False)

        self.update_zoomed_view()


    def calculate_line_thickness(self, ax):
        x_range = abs(ax.get_xlim()[1] - ax.get_xlim()[0])
        y_range = abs(ax.get_ylim()[1] - ax.get_ylim()[0])
        line_thickness = max(0.8, 5 / max(x_range, y_range))
        return line_thickness


    def clearLines(self):
        for line_global, line_zoomed in self.line_objects.values():
            if line_global in self.ax_global.collections:
                line_global.remove()
            if line_zoomed in self.ax_zoomed.collections:
                line_zoomed.remove()
        
        if self.ax_zoomed.get_legend() is not None:
            self.ax_zoomed.get_legend().remove()
        self.drawn_paths.clear()
        self.line_objects.clear()
        self.kdtrees.clear()
        self.recordcount = 0
        self.legend_handles = []
        self.others_legend_added = False
        self.reset_view()
        

    def on_scroll(self, event):
        if event.button == 'up':
            self.zoom_in(event.xdata, event.ydata)
        else:
            self.zoom_out(event.xdata, event.ydata)


    def zoom_in(self, x, y):
        if x is None or y is None:
            return
        scale_factor = 0.9
        x0, x1 = self.ax_zoomed.get_xlim()
        y0, y1 = self.ax_zoomed.get_ylim()
        self.ax_zoomed.set_xlim([x - (x - x0) * scale_factor, x + (x1 - x) * scale_factor])
        self.ax_zoomed.set_ylim([y - (y - y0) * scale_factor, y + (y1 - y) * scale_factor])
        self.fig_zoomed.canvas.draw_idle()


    def zoom_out(self, x, y):
        if x is None or y is None:
            return
        scale_factor = 1.1
        x0, x1 = self.ax_zoomed.get_xlim()
        y0, y1 = self.ax_zoomed.get_ylim()
        self.ax_zoomed.set_xlim([x - (x - x0) * scale_factor, x + (x1 - x) * scale_factor])
        self.ax_zoomed.set_ylim([y - (y - y0) * scale_factor, y + (y1 - y) * scale_factor])
        self.fig_zoomed.canvas.draw_idle()


    def on_click(self, event):
        self.ctrl_pressed = QApplication.keyboardModifiers() & Qt.ControlModifier
        if event.button == 1 and event.xdata is not None and event.ydata is not None:  # Left mouse button.
            self.pressed = True
            self.x0 = event.xdata
            self.y0 = event.ydata

            if self.ctrl_pressed:   # If Ctrl key is pressed, enable panning
                self.orig_xlim = self.ax_zoomed.get_xlim()
                self.orig_ylim = self.ax_zoomed.get_ylim()
                self.is_panning = True
            else:  # If Ctrl key is not pressed, enable box zoom
                if hasattr(self, 'rect') and self.rect is not None:
                    self.rect.remove()
                self.rect = Rectangle((self.x0, self.y0), 0, 0, edgecolor='red', facecolor='none', zorder=3)
                self.ax_zoomed.add_patch(self.rect)

            self.fig_zoomed.canvas.draw_idle()


    def check_click_on_line(self, event):
        if event.xdata is None or event.ydata is None:
            return 
        self.highlight_nearest_line(event)


    def on_mouse_move(self, event):
        current_time = time.time()
        if current_time - self.last_check < 0.1:  # check per 0.1 second
            return
        self.last_check = current_time
        if self.pressed:
            # Ensure the mouse position is valid
            if event.xdata is not None and event.ydata is not None:
                if self.ctrl_pressed and self.is_panning:
                    # Only record the current mouse position, no drawing
                    self.current_x = event.xdata
                    self.current_y = event.ydata

                elif not self.ctrl_pressed and self.rect is not None:
                    # Update the size of the box zoom rectangle
                    width = event.xdata - self.x0
                    height = event.ydata - self.y0
                    self.rect.set_width(width)
                    self.rect.set_height(height)
                    self.fig_zoomed.canvas.draw_idle()
        else:
            pass


    def highlight_nearest_line(self, event):
        if event.xdata is None or event.ydata is None:
            return
        
        closest_line = None
        min_distance = float('inf')
        
        for id, kdtree, color, line_thickness_zoomed in self.kdtrees:
            distance, index = kdtree.query([event.xdata, event.ydata])
            if distance < min_distance:
                min_distance = distance
                closest_line = (id, color, line_thickness_zoomed)
        
        if closest_line and closest_line != self.current_highlighted_line:
            if self.current_highlighted_line:
                self.reset_line_style(*self.current_highlighted_line)
            
            self.highlight_line(closest_line[0])  # id
            self.current_highlighted_line = closest_line
            record_id = closest_line[0]
            self.recordSelected.emit(record_id)


    def highlight_line(self, id):
        lines = self.line_objects.get(id)
        if not lines:
            return
        
        for line in lines:
            line.set_color('red')
            line.set_linewidth(2)
        
        self.fig_zoomed.canvas.draw_idle()
        self.fig_global.canvas.draw_idle()


    def remove_existing_line(self, id):
        for ax in [self.ax_global, self.ax_zoomed]:
            for line in ax.get_lines():
                if line.get_gid() == id:
                    line.remove()

            
    def reset_line_style(self, id, orig_color, orig_linewidth):
        lines = self.line_objects.get(id)
        if not lines:
            return
        
        for line in lines:
            line.set_color(orig_color)
            line.set_linewidth(orig_linewidth)
        
        self.fig_zoomed.canvas.draw_idle()
        self.fig_global.canvas.draw_idle()


    def on_release(self, event):
        if self.pressed and self.is_panning:
            if self.current_x is not None and self.current_y is not None:
                # Perform panning when the mouse is released if a valid current position is recorded
                dx = self.current_x - self.x0
                dy = self.current_y - self.y0
                cur_xlim = self.ax_zoomed.get_xlim()
                cur_ylim = self.ax_zoomed.get_ylim()
                self.ax_zoomed.set_xlim(cur_xlim[0] - dx, cur_xlim[1] - dx)
                self.ax_zoomed.set_ylim(cur_ylim[0] - dy, cur_ylim[1] - dy)
                self.fig_zoomed.canvas.draw_idle()
                self.is_panning = False
        elif not self.ctrl_pressed and self.rect is not None:
            # Execute box zoom logic
            self.rect.remove()
            x0, y0 = self.x0, self.y0
            x1, y1 = event.xdata, event.ydata
            # Check if the box selection area is large enough
            if x1 is not None and y1 is not None and (abs(x1 - x0) > 1 and abs(y1 - y0) > 1):
                self.ax_zoomed.set_xlim(sorted([x0, x1]))
                self.ax_zoomed.set_ylim(sorted([y0, y1]))
            else:
                # If the box selection area is too small, consider it a click and trigger click event logic
                self.check_click_on_line(event)

            self.maintain_aspect_ratio(self.ax_zoomed)

        self.reset_mouse_variables()
        self.update_zoomed_view()


    def update_zoomed_view(self):
        xlim = self.ax_zoomed.get_xlim()
        ylim = self.ax_zoomed.get_ylim()

        global_xlim = (self.ax_global.dataLim.xmin, self.ax_global.dataLim.xmax)
        global_ylim = (self.ax_global.dataLim.ymin, self.ax_global.dataLim.ymax)

        zoom_exceeds_global = (xlim[0] <= global_xlim[0] and xlim[1] >= global_xlim[1] and
                            ylim[0] <= global_ylim[0] and ylim[1] >= global_ylim[1])

        if zoom_exceeds_global:
            if self.global_rect is not None:
                self.global_rect.remove()
                self.global_rect = None
        else:
            if self.global_rect is not None:
                self.global_rect.remove()

            self.global_rect = Rectangle((xlim[0], ylim[0]), xlim[1] - xlim[0], ylim[1] - ylim[0],
                                    edgecolor='red', facecolor='none', linewidth=1, transform=self.ax_global.transData)
            self.ax_global.add_patch(self.global_rect)

        self.fig_zoomed.canvas.draw_idle()
        self.fig_global.canvas.draw_idle()


    def reset_mouse_variables(self):
        self.pressed = False
        self.x0 = None
        self.y0 = None
        self.orig_xlim = None
        self.orig_ylim = None
        self.current_x = None
        self.current_y = None
        self.ctrl_pressed = False
        self.rect = None


    def reset_view(self):
        self.clear_geotiff()

        self.ax_zoomed.set_xlim(self.ax_global.dataLim.xmin, self.ax_global.dataLim.xmax)
        self.ax_zoomed.set_ylim(self.ax_global.dataLim.ymin, self.ax_global.dataLim.ymax)

        if self.rect is not None:
            if self.rect in self.ax_zoomed.get_children():
                self.rect.remove()
            self.rect = None

        if self.global_rect is not None:
            if self.global_rect in self.ax_global.get_children():
                self.global_rect.remove()
            self.global_rect = None

        self.maintain_aspect_ratio(self.ax_zoomed)
        self.update_zoomed_view()