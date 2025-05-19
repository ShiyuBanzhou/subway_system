import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
from datetime import datetime

CURRENT_USER_ROLE = None # Global variable to store user role

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dbfinal'
}

def show_login_dialog():
    login = tk.Tk()
    login.title("地铁管理系统账户登录")
    login.geometry("400x200") # Adjusted height slightly for better padding
    tk.Label(login, text="账号:").grid(row=0, column=0, padx=10, pady=(15,5), sticky=tk.W)
    user_var = tk.StringVar()
    user_var.set('passenger_user') 
    user_entry = tk.Entry(login, textvariable=user_var, width=30)
    user_entry.grid(row=0, column=1, padx=10, pady=(15,5), sticky=tk.EW)
    
    tk.Label(login, text="密码:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
    pwd_var = tk.StringVar()
    pwd_var.set('password123') 
    pwd_entry = tk.Entry(login, textvariable=pwd_var, show="*", width=30)
    pwd_entry.grid(row=1, column=1, padx=10, pady=5, sticky=tk.EW)
    
    login.grid_columnconfigure(1, weight=1) # Allow entry to expand

    def try_login():
        username = user_var.get()
        password = pwd_var.get()
        if not username or not password:
            messagebox.showerror("错误", "请填写账号和密码")
            return
        
        global DB_CONFIG, CURRENT_USER_ROLE 
        DB_CONFIG['user'] = username
        DB_CONFIG['password'] = password
        
        try:
            conn = mysql.connector.connect(**DB_CONFIG, auth_plugin='mysql_native_password')
            conn.close() 
            
            if username == 'admin_user':
                CURRENT_USER_ROLE = 'admin'
            elif username == 'passenger_user':
                CURRENT_USER_ROLE = 'user'
            else:
                CURRENT_USER_ROLE = 'user' 
            
            messagebox.showinfo("登陆成功", f"欢迎 {username} (角色: {CURRENT_USER_ROLE})！")
            login.destroy()
        except mysql.connector.Error as err:
            messagebox.showerror("登录失败", f"数据库错误: {err}")
            CURRENT_USER_ROLE = None

    tk.Button(login, text="登录", command=try_login).grid(row=2, column=0, columnspan=2, pady=20)
    login.mainloop()


# --- Database Interaction Functions ---
def get_db_connection():
    """Establish database connection"""
    try:
        # Specify the authentication plugin if needed, especially for mysql_native_password
        conn = mysql.connector.connect(**DB_CONFIG, auth_plugin='mysql_native_password')
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Database Connection Error", f"Error: {err}")
        return None

def fetch_data(query, params=None):
    """Execute SELECT query and fetch all results"""
    conn = get_db_connection()
    if conn:
        # Use dictionary cursor for easy column name access
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            results = cursor.fetchall()
            return results
        except mysql.connector.Error as err:
            messagebox.showerror("Query Error", f"Failed to execute query: {err}\nQuery: {query}")
            return []
        finally:
            # Ensure cursor and connection are always closed
            if cursor:
                cursor.close()
            if conn.is_connected():
                conn.close()
    return []

def execute_query(query, params=None):
    """Execute INSERT, UPDATE, DELETE or DDL query"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit() # Commit transaction
            return cursor.lastrowid # For INSERT, return the last inserted ID
        except mysql.connector.Error as err:
            conn.rollback() # Rollback on error
            messagebox.showerror("Execution Error", f"Failed to execute operation: {err}\nStatement: {query}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn.is_connected():
                conn.close()
    return None

def call_stored_procedure(proc_name, args=()):
    """Call a stored procedure"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Call stored procedure and get output parameters
            result_args = cursor.callproc(proc_name, args)
            conn.commit() # Commit as stored procedure might modify data
            return result_args
        except mysql.connector.Error as err:
            conn.rollback()
            messagebox.showerror("Stored Procedure Error", f"Call failed: {err}\nProcedure: {proc_name}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn.is_connected():
                conn.close()
    return None

# --- New Database Interaction Functions ---
def fetch_pois_for_station(station_id):
    """Fetch Points of Interest for a given station ID"""
    query = """
        SELECT poi_name, category, description
        FROM PointsOfInterest
        WHERE station_id = %s
        ORDER BY category, poi_name
    """
    return fetch_data(query, (station_id,))

def find_transfer_lines(station_name, current_line_id):
    """Find other lines the station belongs to (for transfer info)"""
    # Combined logic: find stations with the same name on different lines,
    # where at least one of them is marked as a transfer station.
    query_combined = """
        SELECT DISTINCT l.line_name
        FROM Station s
        JOIN Line l ON s.line_id = l.line_id
        WHERE s.station_name = %s AND s.line_id != %s
          AND EXISTS (SELECT 1 FROM Station s_check WHERE s_check.station_name = s.station_name AND s_check.is_transfer = 1)
        ORDER BY l.line_name
    """
    return fetch_data(query_combined, (station_name, current_line_id))


class SubwayMapMixin:
    def create_map_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="线路地图")

        # 创建 Canvas 和滚动条
        container = ttk.Frame(tab)
        container.pack(fill=tk.BOTH, expand=True)

        self.map_canvas = tk.Canvas(container, bg="#f0f0f0", scrollregion=(0, 0, 1200, 800))
        h_scroll = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=self.map_canvas.xview)
        v_scroll = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.map_canvas.yview)

        self.map_canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

        # 网格布局
        self.map_canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # 调色板
        palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

        # 获取线路数据
        lines = fetch_data("SELECT line_id, line_name FROM `line` WHERE status='运营' ORDER BY line_id")
        self.map_objects = []
        self.map_station_names = set()

        # 绘制每条线路
        for line_idx, line in enumerate(lines):
            line_id = line['line_id']
            line_name = line['line_name']
            color = palette[line_idx % len(palette)]

            # 获取该线路的所有站点
            stations = fetch_data(
                "SELECT station_id, station_name FROM station WHERE line_id=%s ORDER BY station_id",
                (line_id,)
            )

            if not stations:
                continue

            # 计算初始坐标
            start_x = 100
            line_y = 100 + line_idx * 120

            # 绘制连接线
            line_coords = []
            for station_idx, station in enumerate(stations):
                station_x = start_x + station_idx * 150
                line_coords.extend([station_x, line_y])

            # 绘制线路
            if len(line_coords) >= 4:
                self.map_canvas.create_line(
                    *line_coords,
                    fill=color,
                    width=8,
                    capstyle=tk.ROUND,
                    tags=(f'line_{line_id}', 'subway_line')
                )

            # 绘制站点和站名
            for station_idx, station in enumerate(stations):
                station_x = start_x + station_idx * 150
                station_name = station['station_name']
                self.map_station_names.add(station_name)

                # 站点圆点
                self.map_canvas.create_oval(
                    station_x - 10, line_y - 10, station_x + 10, line_y + 10,
                    fill='white', outline=color, width=3,
                    tags=('station_dot', station_name, f'station_{station["station_id"]}')
                )

                # 站名标签
                label_y_offset = -25 if line_idx % 2 == 0 else 25
                self.map_canvas.create_text(
                    station_x, line_y + label_y_offset,
                    text=station_name,
                    font=('Helvetica', 10, 'bold'),
                    fill=color,
                    tags=('station_text', station_name)
                )

                # 线路名称标签
                if station_idx == 0:
                    self.map_canvas.create_text(
                        station_x - 35, line_y - 35,
                        text=line_name,
                        font=('Helvetica', 12, 'bold'),
                        fill=color,
                        angle=45,
                        tags=(f'line_label_{line_id}', 'line_label')
                    )

        # 更新滚动区域
        self.map_canvas.update_idletasks()
        self.center_content()

        # 绑定事件
        self.map_canvas.tag_bind('station_dot', '<Button-1>', self.on_map_station_click)

    def center_content(self):
        """将内容居中显示"""
        bbox = self.map_canvas.bbox('all')
        if bbox:
            canvas_width = self.map_canvas.winfo_width()
            canvas_height = self.map_canvas.winfo_height()

            content_width = bbox[2] - bbox[0]
            content_height = bbox[3] - bbox[1]

            # 计算居中位置的比例
            x_frac = (bbox[0] + (content_width - canvas_width) / 2) / content_width
            y_frac = (bbox[1] + (content_height - canvas_height) / 2) / content_height

            # 使用 moveto 方法滚动到中心
            self.map_canvas.xview_moveto(max(0, min(1, x_frac)))
            self.map_canvas.yview_moveto(max(0, min(1, y_frac)))

    def on_map_station_click(self, event):
        """点击站点的事件处理"""
        item = self.map_canvas.find_closest(event.x, event.y)[0]
        tags = self.map_canvas.gettags(item)

        # 查找站名标签
        for tag in tags:
            if tag in self.map_station_names:
                self.show_station_popup(tag)
                break

    def show_station_popup(self, station_name):
        # 弹窗展示站点详情及 POI
        info = fetch_data(
            "SELECT station_id, location_desc, is_transfer FROM station WHERE station_name=%s", (station_name,)
        )
        if not info:
            messagebox.showerror("查询错误", f"未找到站点 '{station_name}'。")
            return
        st = info[0]
        pois = fetch_data(
            "SELECT poi_name, category FROM pointsofinterest WHERE station_id=%s", (st['station_id'],)
        )
        text = f"站点: {station_name}\n位置: {st['location_desc']}\n换乘站: {'是' if st['is_transfer'] else '否'}\n\n周边兴趣点:\n"
        text += ''.join([f"• {p['poi_name']} ({p['category']})\n" for p in pois]) if pois else '无'
        messagebox.showinfo(f"{station_name} 信息", text)

# --- GUI Application Class ---
class SubwayApp(SubwayMapMixin, tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("地铁信息管理系统 (增强版)")
        self.geometry("1080x720")

        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Transfer.Treeview', foreground='blue', font=('TkDefaultFont', 10, 'bold'))
        style.configure('Normal.Treeview', font=('TkDefaultFont', 10))
        style.map('Transfer.Treeview', background=[('selected', '#ADD8E6')], foreground=[('selected', 'black')])
        style.map('Normal.Treeview', background=[('selected', '#ADD8E6')], foreground=[('selected', 'black')])
        
        # Style for alternating row colors in Treeviews
        style.configure("oddrow.Treeview", background="#f0f0f0") # Light grey for odd rows
        # Even rows will use the default Treeview background (typically white)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        self.station_details = {}
        self.train_form_line_data = {} 
        self.staff_form_widgets = {} 
        self.staff_roles = ['司机', '站务员', '维修工程师', '清洁员', '票务员', '经理', '管理员']
        self.staff_statuses = ['在职', '离职', '休假']

        self.assignment_form_widgets = {}
        self.assignment_staff_data = {} 
        self.assignment_station_data = {} 
        self.shift_types = ['早班', '中班', '晚班', '全天', '休息'] 

        global CURRENT_USER_ROLE
        self.create_line_station_tab()
        self.create_schedule_tab()
        self.create_ticket_tab()
        # self.create_fare_tab() # 此标签页未实现，暂时注释掉
        self.create_alert_tab()
        self.create_turnstile_tab()
        self.create_map_tab()

        if CURRENT_USER_ROLE == 'admin':
            self.create_train_admin_tab()
            self.create_staff_tab()
            self.create_maint_tab() 
        elif CURRENT_USER_ROLE == 'user':
            pass 

    # --- Tab 1: Lines, Stations & Surroundings (Enhanced) ---
    def create_line_station_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="线路、站点与周边")

        # Top Frame for Line Selection
        line_frame = ttk.LabelFrame(tab, text="选择线路")
        line_frame.pack(pady=5, padx=10, fill="x")

        ttk.Label(line_frame, text="选择线路:").pack(side=tk.LEFT, padx=5)
        self.line_combobox = ttk.Combobox(line_frame, state="readonly", width=30)
        self.line_combobox.pack(side=tk.LEFT, padx=5)
        self.line_combobox.bind("<<ComboboxSelected>>", self.load_stations_for_line)
        # self.load_lines() # Moved after station_tree creation

        # Main content frame (using PanedWindow for resizing)
        main_pane = ttk.PanedWindow(tab, orient=tk.HORIZONTAL)
        main_pane.pack(pady=5, padx=10, fill="both", expand=True)

        # Left Pane: Station List
        station_list_frame = ttk.Frame(main_pane, width=450) # Initial width
        main_pane.add(station_list_frame, weight=2) # Give more weight

        station_frame = ttk.LabelFrame(station_list_frame, text="站点列表 (换乘站以蓝色粗体显示)")
        station_frame.pack(pady=5, padx=5, fill="both", expand=True)

        cols = ('station_name', 'location_desc') # Using styling for transfer indication
        self.station_tree = ttk.Treeview(station_frame, columns=cols, show='headings', height=20, selectmode="browse")
        self.station_tree.heading('station_name', text='站点名称')
        self.station_tree.heading('location_desc', text='位置描述')
        self.station_tree.column('station_name', width=150, stretch=tk.NO)
        self.station_tree.column('location_desc', width=280)

        # Scrollbar for Station Tree
        scrollbar_station = ttk.Scrollbar(station_frame, orient=tk.VERTICAL, command=self.station_tree.yview)
        self.station_tree.configure(yscroll=scrollbar_station.set)
        scrollbar_station.pack(side=tk.RIGHT, fill=tk.Y)
        self.station_tree.pack(side=tk.LEFT, fill="both", expand=True)
        self.station_tree.bind('<<TreeviewSelect>>', self.on_station_select) # Bind selection event

        # --- !!! MOVED load_lines() CALL HERE !!! ---
        # Load lines and initial station data AFTER station_tree is created
        self.load_lines()

        # Right Pane: Station Details (POI and Transfer)
        details_frame = ttk.Frame(main_pane, width=450) # Initial width
        main_pane.add(details_frame, weight=3) # Give slightly more weight

        # Transfer Info Frame
        transfer_info_frame = ttk.LabelFrame(details_frame, text="换乘信息")
        transfer_info_frame.pack(pady=5, padx=5, fill="x")
        self.transfer_button = ttk.Button(transfer_info_frame, text="查找可换乘线路", state=tk.DISABLED, command=self.show_transfer_lines)
        self.transfer_button.pack(pady=5)
        self.transfer_label = ttk.Label(transfer_info_frame, text="请先在左侧选择一个换乘站", wraplength=400, justify=tk.LEFT)
        self.transfer_label.pack(pady=5, padx=5, fill='x')


        # POI Frame
        poi_frame = ttk.LabelFrame(details_frame, text="周边兴趣点 (POI)")
        poi_frame.pack(pady=10, padx=5, fill="both", expand=True)

        cols_poi = ('poi_name', 'category', 'description')
        self.poi_tree = ttk.Treeview(poi_frame, columns=cols_poi, show='headings', height=15)
        self.poi_tree.heading('poi_name', text='名称')
        self.poi_tree.heading('category', text='分类')
        self.poi_tree.heading('description', text='描述')
        self.poi_tree.column('poi_name', width=150, stretch=tk.NO)
        self.poi_tree.column('category', width=80, anchor=tk.CENTER)
        self.poi_tree.column('description', width=200)

        # Scrollbar for POI Tree
        scrollbar_poi = ttk.Scrollbar(poi_frame, orient=tk.VERTICAL, command=self.poi_tree.yview)
        self.poi_tree.configure(yscroll=scrollbar_poi.set)
        scrollbar_poi.pack(side=tk.RIGHT, fill=tk.Y)
        self.poi_tree.pack(side=tk.LEFT, fill="both", expand=True)


    def load_lines(self):
        """Load all lines into the combobox"""
        lines = fetch_data("SELECT line_id, line_name FROM Line WHERE status = '运营' ORDER BY line_name")
        self.line_data = {line['line_name']: line['line_id'] for line in lines}
        self.line_combobox['values'] = list(self.line_data.keys())
        if self.line_combobox['values']:
            self.line_combobox.current(0) # Default to the first line
            self.load_stations_for_line() # Load stations for the default line

    def load_stations_for_line(self, event=None):
        """Load station info based on the selected line"""
        selected_line_name = self.line_combobox.get()
        if not selected_line_name:
            return
        line_id = self.line_data.get(selected_line_name)

        # Clear old data
        self.station_details.clear() # Clear stored details
        # --- Check if station_tree exists before trying to delete children ---
        if hasattr(self, 'station_tree'):
            for i in self.station_tree.get_children():
                self.station_tree.delete(i)
        # Clear POI and transfer info as well
        if hasattr(self, 'poi_tree'):
            for i in self.poi_tree.get_children():
                self.poi_tree.delete(i)
        if hasattr(self, 'transfer_button'):
             self.transfer_button.config(state=tk.DISABLED)
        if hasattr(self, 'transfer_label'):
            self.transfer_label.config(text="请先在左侧选择一个换乘站")


        if line_id and hasattr(self, 'station_tree'): # Ensure station_tree exists
            query = "SELECT station_id, station_name, location_desc, is_transfer FROM Station WHERE line_id = %s ORDER BY station_id"
            stations = fetch_data(query, (line_id,))
            for idx, station in enumerate(stations):
                base_style_tag = 'Transfer.Treeview' if station['is_transfer'] else 'Normal.Treeview'
                row_visual_tag = 'oddrow.Treeview' if idx % 2 != 0 else ()
                tags_to_apply = (base_style_tag,) + ((row_visual_tag,) if row_visual_tag else ())
                
                item_id = self.station_tree.insert('', tk.END, values=(
                    station['station_name'],
                    station['location_desc'] if station['location_desc'] else '暂无描述'
                ), tags=tags_to_apply)
                self.station_details[item_id] = {
                    'id': station['station_id'],
                    'name': station['station_name'],
                    'is_transfer': station['is_transfer'],
                    'line_id': line_id
                }

    def on_station_select(self, event=None):
        """Called when a station is selected in the Treeview"""
        # Ensure widgets exist before accessing them
        if not hasattr(self, 'station_tree') or not hasattr(self, 'poi_tree') or \
           not hasattr(self, 'transfer_button') or not hasattr(self, 'transfer_label'):
            return # Widgets not ready yet

        selected_items = self.station_tree.selection()
        if not selected_items:
            if hasattr(self, 'transfer_button'): self.transfer_button.config(state=tk.DISABLED)
            if hasattr(self, 'transfer_label'): self.transfer_label.config(text="请先在左侧选择一个换乘站")
            if hasattr(self, 'poi_tree'):
                 for i in self.poi_tree.get_children(): self.poi_tree.delete(i)
            return
        item_id = selected_items[0] # Get the internal ID of the selected item
        station_info = self.station_details.get(item_id)

        if station_info:
            station_id = station_info['id']
            station_name = station_info['name']
            is_transfer = station_info['is_transfer']

            if hasattr(self, 'poi_tree'):
                for i in self.poi_tree.get_children(): self.poi_tree.delete(i)
                pois = fetch_pois_for_station(station_id)
                if pois:
                    for idx, poi in enumerate(pois):
                        row_visual_tag = 'oddrow.Treeview' if idx % 2 != 0 else ()
                        tags_to_apply = (row_visual_tag,) if row_visual_tag else ()
                        self.poi_tree.insert('', tk.END, values=(
                            poi['poi_name'],
                            poi['category'] if poi['category'] else '其他',
                            poi['description'] if poi['description'] else ''
                        ), tags=tags_to_apply)
                else:
                     self.poi_tree.insert('', tk.END, values=('该站点暂无周边信息记录', '', ''), tags=('placeholder',))
            
            if hasattr(self, 'transfer_button') and hasattr(self, 'transfer_label'):
                if is_transfer:
                    self.transfer_button.config(state=tk.NORMAL)
                    self.transfer_label.config(text=f"站点 '{station_name}' 是换乘站。\n点击按钮查找其他可换乘线路。")
                else:
                    self.transfer_button.config(state=tk.DISABLED)
                    self.transfer_label.config(text=f"站点 '{station_name}' 不是换乘站。")
        else:
            # Handle case where item_id might not be in dictionary
            self.transfer_button.config(state=tk.DISABLED)
            self.transfer_label.config(text="无法获取所选站点信息。")
            for i in self.poi_tree.get_children():
                self.poi_tree.delete(i)

    def show_transfer_lines(self):
        """Find and display other lines for the selected transfer station"""
        if not hasattr(self, 'station_tree'): return # Safety check

        selected_items = self.station_tree.selection()
        if not selected_items: return # Button should be disabled anyway

        item_id = selected_items[0]
        station_info = self.station_details.get(item_id)

        if station_info and station_info['is_transfer']:
            station_name = station_info['name']
            current_line_id = station_info['line_id']
            transfer_lines = find_transfer_lines(station_name, current_line_id)

            if transfer_lines:
                lines_str = ", ".join([line['line_name'] for line in transfer_lines])
                messagebox.showinfo("可换乘线路", f"站点 '{station_name}' 还可换乘以下线路：\n\n{lines_str}")
                if hasattr(self, 'transfer_label'):
                     self.transfer_label.config(text=f"站点 '{station_name}' 可换乘: {lines_str}")
            else:
                messagebox.showinfo("无其他换乘线路", f"在数据库中未找到站点 '{station_name}' 的其他换乘线路信息。\n(可能原因：数据库中其他线路未将此站标记为换乘站，或无同名站点)")
                if hasattr(self, 'transfer_label'):
                    self.transfer_label.config(text=f"站点 '{station_name}' 暂未查询到其他可换乘线路。")
        # else: Button should be disabled if not a transfer station or no selection


    # --- Tab 2: Schedule Query (Mostly unchanged) ---
    def create_schedule_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="时刻表查询")

        # Input Frame
        input_frame = ttk.LabelFrame(tab, text="查询条件")
        input_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(input_frame, text="选择站点:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.schedule_station_combobox = ttk.Combobox(input_frame, state="readonly", width=30)
        self.schedule_station_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.load_all_stations() # Load all stations into combobox

        ttk.Label(input_frame, text="选择日期:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.schedule_date_entry = ttk.Entry(input_frame, width=15)
        self.schedule_date_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.schedule_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d')) # Default to today
        
        # 添加日期选择按钮
        date_button = ttk.Button(input_frame, text="查看可用日期", command=self.show_available_dates)
        date_button.grid(row=1, column=2, padx=5, pady=5)

        search_button = ttk.Button(input_frame, text="查询时刻表", command=self.load_schedule)
        search_button.grid(row=2, column=1, padx=5, pady=5)

        # Schedule Display
        schedule_frame = ttk.LabelFrame(tab, text="列车时刻")
        schedule_frame.pack(pady=10, padx=10, fill="both", expand=True)

        cols_schedule = ('train_number', 'line_name', 'arrival_time', 'departure_time')
        # --- RENAME schedule_tree to avoid conflict if needed, but should be ok ---
        self.schedule_display_tree = ttk.Treeview(schedule_frame, columns=cols_schedule, show='headings', height=15)
        self.schedule_display_tree.heading('train_number', text='列车号')
        self.schedule_display_tree.heading('line_name', text='所属线路')
        self.schedule_display_tree.heading('arrival_time', text='到达时间')
        self.schedule_display_tree.heading('departure_time', text='出发时间')
        self.schedule_display_tree.column('train_number', width=100)
        self.schedule_display_tree.column('line_name', width=150)
        self.schedule_display_tree.column('arrival_time', width=100, anchor=tk.CENTER)
        self.schedule_display_tree.column('departure_time', width=100, anchor=tk.CENTER)

        scrollbar_schedule = ttk.Scrollbar(schedule_frame, orient=tk.VERTICAL, command=self.schedule_display_tree.yview)
        self.schedule_display_tree.configure(yscroll=scrollbar_schedule.set)
        scrollbar_schedule.pack(side=tk.RIGHT, fill=tk.Y)
        self.schedule_display_tree.pack(side=tk.LEFT, fill="both", expand=True)

    def show_available_dates(self):
        """显示包含列车时刻表的日期"""
        query = "SELECT DISTINCT schedule_date FROM Schedule ORDER BY schedule_date"
        dates = fetch_data(query)
        
        if not dates:
            messagebox.showinfo("无可用日期", "数据库中没有找到时刻表数据。")
            return
            
        date_list = [date['schedule_date'].strftime('%Y-%m-%d') for date in dates]
        date_str = "\n".join(date_list)
        
        # 创建包含日期列表的对话框
        date_dialog = tk.Toplevel(self)
        date_dialog.title("可用日期")
        date_dialog.geometry("300x400")
        
        # 标签说明
        ttk.Label(date_dialog, text="以下日期包含列车时刻表：", font=('TkDefaultFont', 10, 'bold')).pack(pady=10)
        
        # 使用Listbox显示日期
        date_listbox = tk.Listbox(date_dialog, width=20, height=15)
        date_listbox.pack(pady=5, padx=10, fill="both", expand=True)
        
        # 添加日期到列表
        for date in date_list:
            date_listbox.insert(tk.END, date)
            
        # 滚动条
        scrollbar = ttk.Scrollbar(date_listbox, orient=tk.VERTICAL, command=date_listbox.yview)
        date_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 双击日期时设置到输入框
        def on_date_select(event):
            selected_idx = date_listbox.curselection()
            if selected_idx:
                selected_date = date_listbox.get(selected_idx[0])
                self.schedule_date_entry.delete(0, tk.END)
                self.schedule_date_entry.insert(0, selected_date)
                date_dialog.destroy()
                
        date_listbox.bind('<Double-1>', on_date_select)
        
        # 关闭按钮
        ttk.Button(date_dialog, text="关闭", command=date_dialog.destroy).pack(pady=10)

    def load_all_stations(self):
        """Load all station names into the schedule query combobox"""
        stations = fetch_data("SELECT station_id, station_name FROM Station ORDER BY station_name")
        self.schedule_station_data = {s['station_name']: s['station_id'] for s in stations}
        # Ensure the combobox exists before setting values
        if hasattr(self, 'schedule_station_combobox'):
            self.schedule_station_combobox['values'] = list(self.schedule_station_data.keys())
            if self.schedule_station_combobox['values']:
                self.schedule_station_combobox.current(0) # Default to the first station

    def load_schedule(self):
        """Load the schedule for the selected station and date"""
        # Ensure widgets exist
        if not hasattr(self, 'schedule_station_combobox') or \
           not hasattr(self, 'schedule_date_entry') or \
           not hasattr(self, 'schedule_display_tree'):
             return

        selected_station_name = self.schedule_station_combobox.get()
        selected_date_str = self.schedule_date_entry.get()

        if not selected_station_name or not selected_date_str:
            messagebox.showwarning("Input Incomplete", "请选择站点并输入日期 (YYYY-MM-DD)。")
            return

        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            messagebox.showerror("Date Format Error", "请输入有效的日期格式 (YYYY-MM-DD)。")
            return

        station_id = self.schedule_station_data.get(selected_station_name)

        # Clear old data
        for i in self.schedule_display_tree.get_children():
            self.schedule_display_tree.delete(i)

        if station_id:
            query = "SELECT t.train_number, l.line_name, sch.arrival_time, sch.departure_time FROM Schedule sch JOIN Train t ON sch.train_id = t.train_id JOIN Station s ON sch.station_id = s.station_id JOIN Line l ON t.line_id = l.line_id WHERE sch.station_id = %s AND sch.schedule_date = %s ORDER BY sch.arrival_time, sch.departure_time"
            schedules = fetch_data(query, (station_id, selected_date))
            if schedules:
                for idx, schedule in enumerate(schedules):
                    arrival_val = schedule['arrival_time']; departure_val = schedule['departure_time']
                    arrival_str = arrival_val.strftime('%H:%M:%S') if hasattr(arrival_val, 'strftime') else str(arrival_val) if arrival_val else "---"
                    departure_str = departure_val.strftime('%H:%M:%S') if hasattr(departure_val, 'strftime') else str(departure_val) if departure_val else "---"
                    row_visual_tag = 'oddrow.Treeview' if idx % 2 != 0 else ()
                    tags_to_apply = (row_visual_tag,) if row_visual_tag else ()
                    self.schedule_display_tree.insert('', tk.END, values=(schedule['train_number'], schedule['line_name'], arrival_str, departure_str), tags=tags_to_apply)
            else:
                 # Insert a placeholder if no schedule found
                 self.schedule_display_tree.insert('', tk.END, values=(f'当天 ({selected_date_str})', '无时刻信息', '', ''), tags=('placeholder',))


    # --- Tab 3: Ticketing (Mostly unchanged, added hints) ---
    def create_ticket_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="票务中心")

        ticket_frame = ttk.LabelFrame(tab, text="购买车票")
        ticket_frame.pack(pady=20, padx=20, fill="x")

        ttk.Label(ticket_frame, text="乘客ID:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.ticket_passenger_id_entry = ttk.Entry(ticket_frame, width=10)
        self.ticket_passenger_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(ticket_frame, text="(请输入已注册乘客的数字ID)").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        # 添加乘客选择下拉框
        ttk.Label(ticket_frame, text="或选择乘客:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.passenger_combobox = ttk.Combobox(ticket_frame, state="readonly", width=30)
        self.passenger_combobox.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        self.passenger_combobox.bind("<<ComboboxSelected>>", self.on_passenger_selected)
        
        # 乘客信息刷新按钮
        refresh_button = ttk.Button(ticket_frame, text="刷新乘客列表", command=self.load_passengers)
        refresh_button.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(ticket_frame, text="出发站:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.ticket_dep_station_combobox = ttk.Combobox(ticket_frame, state="readonly", width=30)
        self.ticket_dep_station_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.ticket_dep_station_combobox.bind("<<ComboboxSelected>>", self.update_estimated_fare)

        ttk.Label(ticket_frame, text="到达站:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.ticket_arr_station_combobox = ttk.Combobox(ticket_frame, state="readonly", width=30)
        self.ticket_arr_station_combobox.grid(row=3, column=1, padx=5, pady=5)
        self.ticket_arr_station_combobox.bind("<<ComboboxSelected>>", self.update_estimated_fare)

        ttk.Label(ticket_frame, text="票种:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.ticket_type_combobox = ttk.Combobox(ticket_frame, state="readonly", width=30)
        self.ticket_type_combobox.grid(row=4, column=1, padx=5, pady=5)
        self.ticket_type_combobox.bind("<<ComboboxSelected>>", self.update_estimated_fare)
        
        # Label to display estimated fare
        self.estimated_fare_label = ttk.Label(ticket_frame, text="预估票价: --.-- 元", font=("TkDefaultFont", 10, "bold"))
        self.estimated_fare_label.grid(row=5, column=0, columnspan=3, padx=5, pady=(10,0), sticky=tk.W)

        # Buy button now at row 6
        buy_button = ttk.Button(ticket_frame, text="确认购买", command=self.buy_ticket) # Removed fare text from button
        buy_button.grid(row=6, column=0, columnspan=3, pady=10) # Updated row index
        
        # 添加购票记录展示区
        ticket_history_frame = ttk.LabelFrame(tab, text="已购票记录")
        ticket_history_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        cols_ticket = ('ticket_id', 'passenger_name', 'departure', 'arrival', 'price', 'ticket_type', 'purchase_time', 'status')
        self.ticket_history_tree = ttk.Treeview(ticket_history_frame, columns=cols_ticket, show='headings', height=8)
        
        self.ticket_history_tree.heading('ticket_id', text='票ID')
        self.ticket_history_tree.heading('passenger_name', text='乘客')
        self.ticket_history_tree.heading('departure', text='出发站')
        self.ticket_history_tree.heading('arrival', text='到达站')
        self.ticket_history_tree.heading('price', text='票价')
        self.ticket_history_tree.heading('ticket_type', text='票种')
        self.ticket_history_tree.heading('purchase_time', text='购买时间')
        self.ticket_history_tree.heading('status', text='状态')
        
        self.ticket_history_tree.column('ticket_id', width=50, stretch=tk.NO)
        self.ticket_history_tree.column('passenger_name', width=80)
        self.ticket_history_tree.column('departure', width=100)
        self.ticket_history_tree.column('arrival', width=100)
        self.ticket_history_tree.column('price', width=60, anchor=tk.E)
        self.ticket_history_tree.column('ticket_type', width=80)
        self.ticket_history_tree.column('purchase_time', width=130)
        self.ticket_history_tree.column('status', width=70, anchor=tk.CENTER)
        
        scrollbar_ticket = ttk.Scrollbar(ticket_history_frame, orient=tk.VERTICAL, command=self.ticket_history_tree.yview)
        self.ticket_history_tree.configure(yscroll=scrollbar_ticket.set)
        scrollbar_ticket.pack(side=tk.RIGHT, fill=tk.Y)
        self.ticket_history_tree.pack(side=tk.LEFT, fill="both", expand=True)
        
        # 刷新票据按钮
        refresh_tickets_button = ttk.Button(ticket_history_frame, text="刷新票据记录", 
                                          command=self.load_ticket_history)
        refresh_tickets_button.pack(side=tk.BOTTOM, pady=5)

        self.load_stations_for_ticketing() # This will call update_estimated_fare indirectly via combobox.set if needed
        self.load_ticket_types()           # This will also call update_estimated_fare if it sets a default
        self.load_passengers()             # Load passenger data
        self.load_ticket_history()         # Load ticket history
    
    def load_passengers(self):
        """加载所有乘客数据"""
        query = "SELECT passenger_id, name, phone_number FROM Passenger ORDER BY passenger_id"
        passengers = fetch_data(query)
        
        if passengers:
            self.passenger_data = {}
            passenger_display_list = []
            
            for p in passengers:
                display_text = f"{p['name']} (ID: {p['passenger_id']}, 手机: {p['phone_number']})"
                passenger_display_list.append(display_text)
                self.passenger_data[display_text] = p['passenger_id']
                
            if hasattr(self, 'passenger_combobox'):
                self.passenger_combobox['values'] = passenger_display_list
                if passenger_display_list:
                    self.passenger_combobox.current(0)  # 默认选择第一个乘客
        else:
            if hasattr(self, 'passenger_combobox'):
                self.passenger_combobox['values'] = ["无乘客数据"]
                self.passenger_combobox.current(0)
    
    def on_passenger_selected(self, event=None):
        """当从下拉框选择乘客时，自动填充乘客ID"""
        selected_passenger = self.passenger_combobox.get()
        if selected_passenger and selected_passenger != "无乘客数据" and hasattr(self, 'passenger_data'):
            passenger_id = self.passenger_data.get(selected_passenger)
            if passenger_id:
                self.ticket_passenger_id_entry.delete(0, tk.END)
                self.ticket_passenger_id_entry.insert(0, str(passenger_id))
    
    def load_ticket_history(self):
        """加载票务记录"""
        # 清空现有记录
        for item in self.ticket_history_tree.get_children():
            self.ticket_history_tree.delete(item)
            
        # 查询票务记录
        query = """
        SELECT t.ticket_id, p.name as passenger_name, 
               s1.station_name as departure_station, 
               s2.station_name as arrival_station,
               t.price, tt.type_name, 
               DATE_FORMAT(t.purchase_time, '%Y-%m-%d %H:%i:%s') as purchase_time,
               t.payment_status
        FROM Ticket t
        JOIN Passenger p ON t.passenger_id = p.passenger_id
        JOIN Station s1 ON t.departure_station_id = s1.station_id
        JOIN Station s2 ON t.arrival_station_id = s2.station_id
        LEFT JOIN TicketType tt ON t.ticket_type_id = tt.type_id
        ORDER BY t.purchase_time DESC
        LIMIT 100
        """
        
        tickets = fetch_data(query)
        
        if tickets:
            for idx, ticket in enumerate(tickets):
                # 交替行颜色
                row_visual_tag = 'oddrow.Treeview' if idx % 2 != 0 else ()
                tags_to_apply = (row_visual_tag,) if row_visual_tag else ()
                
                self.ticket_history_tree.insert('', tk.END, values=(
                    ticket['ticket_id'],
                    ticket['passenger_name'],
                    ticket['departure_station'],
                    ticket['arrival_station'],
                    f"{ticket['price']:.2f}",
                    ticket['type_name'] if ticket['type_name'] else '未知',
                    ticket['purchase_time'],
                    ticket['payment_status']
                ), tags=tags_to_apply)
        else:
            self.ticket_history_tree.insert('', tk.END, values=('--', '无票务记录', '', '', '', '', '', ''))

    def load_ticket_types(self):
        """Load all ticket types into the ticketing combobox"""
        ticket_types = fetch_data("SELECT type_id, type_name FROM TicketType ORDER BY type_id")
        if ticket_types:
            self.ticket_type_names = [tt['type_name'] for tt in ticket_types]
            self.ticket_type_data = {tt['type_name']: tt['type_id'] for tt in ticket_types}
            
            if hasattr(self, 'ticket_type_combobox'):
                self.ticket_type_combobox['values'] = self.ticket_type_names
                if self.ticket_type_names:
                    self.ticket_type_combobox.current(0)
                    self.update_estimated_fare() # Update fare after setting default ticket type
        else:
            self.ticket_type_names = []
            self.ticket_type_data = {}
            if hasattr(self, 'ticket_type_combobox'):
                self.ticket_type_combobox['values'] = []
                self.ticket_type_combobox.set("无可用票种")
            self.update_estimated_fare() # Clear/update fare if no ticket types

    def load_stations_for_ticketing(self):
        """Load all station names into the ticketing comboboxes"""
        stations = fetch_data("SELECT station_id, station_name FROM Station ORDER BY station_name")
        station_names = [s['station_name'] for s in stations]
        self.ticket_station_data = {s['station_name']: s['station_id'] for s in stations}

        if hasattr(self, 'ticket_dep_station_combobox') and hasattr(self, 'ticket_arr_station_combobox'):
            self.ticket_dep_station_combobox['values'] = station_names
            self.ticket_arr_station_combobox['values'] = station_names
            if station_names:
                self.ticket_dep_station_combobox.current(0)
                self.ticket_arr_station_combobox.current(1 if len(station_names) > 1 else 0)
                self.update_estimated_fare() # Update fare after setting default stations
            else:
                self.update_estimated_fare() # Clear/update fare if no stations

    def update_estimated_fare(self, event=None): # event parameter for binding
        if not hasattr(self, 'ticket_dep_station_combobox') or \
           not hasattr(self, 'ticket_arr_station_combobox') or \
           not hasattr(self, 'ticket_type_combobox') or \
           not hasattr(self, 'estimated_fare_label') or \
           not hasattr(self, 'ticket_station_data') or \
           not hasattr(self, 'ticket_type_data'):
            if hasattr(self, 'estimated_fare_label'): # Check if label exists to avoid error on early calls
                 self.estimated_fare_label.config(text="预估票价: 等待选择...")
            return

        dep_station_name = self.ticket_dep_station_combobox.get()
        arr_station_name = self.ticket_arr_station_combobox.get()
        ticket_type_name = self.ticket_type_combobox.get()

        if not dep_station_name or not arr_station_name or not ticket_type_name or \
           dep_station_name == "无可用站点" or ticket_type_name == "无可用票种": # Check for placeholder text
            self.estimated_fare_label.config(text="预估票价: 请完成选择")
            return

        dep_station_id = self.ticket_station_data.get(dep_station_name)
        arr_station_id = self.ticket_station_data.get(arr_station_name)
        ticket_type_id = self.ticket_type_data.get(ticket_type_name)

        if dep_station_id is None or arr_station_id is None or ticket_type_id is None:
            self.estimated_fare_label.config(text="预估票价: 选择无效")
            return

        # Args for sp_calculate_fare: (dep_id, arr_id, type_id, OUT price, OUT message)
        # The OUT params need initial dummy values of the correct type for callproc.
        args = (dep_station_id, arr_station_id, ticket_type_id, 0.0, '') 
        results = call_stored_procedure('sp_calculate_fare', args)

        if results:
            calculated_price = results[3] # 4th element (0-indexed)
            message = results[4]          # 5th element

            if calculated_price is not None and calculated_price >= 0: # Price can be 0 if same station or free
                self.estimated_fare_label.config(text=f"预估票价: {calculated_price:.2f} 元")
            else:
                # Display message from SP if price is not valid
                display_message = message if message else "无法计算票价"
                self.estimated_fare_label.config(text=f"预估票价: {display_message}")
        else:
            self.estimated_fare_label.config(text="预估票价: 计算错误")

    def buy_ticket(self):
        if not hasattr(self, 'ticket_passenger_id_entry') or \
           not hasattr(self, 'ticket_dep_station_combobox') or \
           not hasattr(self, 'ticket_arr_station_combobox') or \
           not hasattr(self, 'ticket_type_combobox'): 
            messagebox.showerror("Internal Error", "票务界面组件未完全初始化。")
            return

        passenger_id_str = self.ticket_passenger_id_entry.get()
        if not passenger_id_str:
             messagebox.showerror("输入错误", "乘客ID不能为空。")
             return

        try:
            passenger_id = int(passenger_id_str)
        except ValueError:
            messagebox.showerror("输入错误", "乘客ID必须是有效的数字。")
            return

        dep_station_name = self.ticket_dep_station_combobox.get()
        arr_station_name = self.ticket_arr_station_combobox.get()
        selected_ticket_type_name = self.ticket_type_combobox.get()

        if not dep_station_name or not arr_station_name:
            messagebox.showwarning("选择不完整", "请选择出发站和到达站。")
            return
        
        if not selected_ticket_type_name or not hasattr(self, 'ticket_type_data') or selected_ticket_type_name == "无可用票种":
            messagebox.showwarning("选择不完整", "请选择有效的票种。")
            return

        dep_station_id = self.ticket_station_data.get(dep_station_name)
        arr_station_id = self.ticket_station_data.get(arr_station_name)
        ticket_type_id = self.ticket_type_data.get(selected_ticket_type_name)

        if not dep_station_id or not arr_station_id:
            messagebox.showerror("内部错误", "无法找到选择的站点ID。")
            return
        
        if ticket_type_id is None:
            messagebox.showerror("内部错误", "无法找到选择的票种ID。")
            return

        args_for_purchase = (passenger_id, dep_station_id, arr_station_id, ticket_type_id, 0, '') 
        results = call_stored_procedure('sp_purchase_ticket', args_for_purchase)

        if results:
            ticket_id_out = results[4] 
            message_out = results[5]   

            if ticket_id_out is not None and ticket_id_out > 0:
                messagebox.showinfo("购票结果", f"{message_out}")
                
                # 生成模拟的闸机入站记录
                self.generate_turnstile_entry(passenger_id, dep_station_id, ticket_id_out)
                
                # 清空乘客ID输入框，刷新票务记录
                self.ticket_passenger_id_entry.delete(0, tk.END)
                if hasattr(self, 'load_ticket_history'):
                    self.load_ticket_history()
            else:
                messagebox.showerror("购票失败", message_out)

    def generate_turnstile_entry(self, passenger_id, station_id, ticket_id):
        """生成模拟的闸机入站记录"""
        # 获取当前时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 插入入站记录
        query = """
        INSERT INTO TurnstileLog (passenger_id, station_id, action, timestamp, ticket_id)
        VALUES (%s, %s, 'IN', %s, %s)
        """
        
        execute_query(query, (passenger_id, station_id, current_time, ticket_id))
    
    def create_turnstile_tab(self):
        tab = ttk.Frame(self.notebook); self.notebook.add(tab, text="闸机日志")
        t_frame = ttk.LabelFrame(tab, text="进出记录"); t_frame.pack(fill="both", expand=True, padx=10, pady=10) # Standard section padding
        
        # 添加筛选控件
        filter_frame = ttk.Frame(t_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="乘客ID:").pack(side=tk.LEFT, padx=5)
        self.turnstile_passenger_id = ttk.Entry(filter_frame, width=10)
        self.turnstile_passenger_id.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filter_frame, text="站点:").pack(side=tk.LEFT, padx=5)
        self.turnstile_station_combobox = ttk.Combobox(filter_frame, state="readonly", width=20)
        self.turnstile_station_combobox.pack(side=tk.LEFT, padx=5)
        
        # 加载所有站点
        station_query = "SELECT station_id, station_name FROM Station ORDER BY station_name"
        stations = fetch_data(station_query)
        if stations:
            self.turnstile_station_data = {s['station_name']: s['station_id'] for s in stations}
            self.turnstile_station_combobox['values'] = ["全部站点"] + list(self.turnstile_station_data.keys())
            self.turnstile_station_combobox.current(0)  # 默认选择"全部站点"
        
        ttk.Button(filter_frame, text="查询", command=self.load_turnstile_logs).pack(side=tk.LEFT, padx=10)
        ttk.Button(filter_frame, text="清除筛选", command=self.clear_turnstile_filter).pack(side=tk.LEFT, padx=5)
        
        # 日志列表
        cols_t = ('log_id','passenger_id','passenger_name','station_name','action','timestamp','ticket_id')
        self.turnstile_tree = ttk.Treeview(t_frame, columns=cols_t, show='headings', height=12)
        headers = ['日志ID','乘客ID','乘客姓名','站点名称','类型','时间','票务ID']
        widths = [80, 80, 100, 150, 80, 150, 80]
        for c, h, w in zip(cols_t, headers, widths):
            self.turnstile_tree.heading(c, text=h)
            self.turnstile_tree.column(c, width=w)
        
        # Scrollbar for turnstile_tree
        turnstile_scrollbar = ttk.Scrollbar(t_frame, orient=tk.VERTICAL, command=self.turnstile_tree.yview)
        self.turnstile_tree.configure(yscrollcommand=turnstile_scrollbar.set)
        turnstile_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.turnstile_tree.pack(side=tk.LEFT, fill="both", expand=True)
        
        # 加载闸机日志数据
        self.load_turnstile_logs()
    
    def clear_turnstile_filter(self):
        """清除闸机日志的筛选条件"""
        if hasattr(self, 'turnstile_passenger_id'):
            self.turnstile_passenger_id.delete(0, tk.END)
        if hasattr(self, 'turnstile_station_combobox'):
            self.turnstile_station_combobox.current(0)  # 切换回"全部站点"
        
        self.load_turnstile_logs()
    
    def load_turnstile_logs(self):
        """加载闸机日志数据，支持筛选"""
        if not hasattr(self, 'turnstile_tree'):
            return
            
        # 清空现有数据
        for i in self.turnstile_tree.get_children():
            self.turnstile_tree.delete(i)
        
        # 构建查询
        base_query = """
        SELECT t.log_id, t.passenger_id, p.name as passenger_name, s.station_name, 
               t.action, DATE_FORMAT(t.timestamp, '%Y-%m-%d %H:%i:%s') as formatted_time, t.ticket_id
        FROM TurnstileLog t
        JOIN Passenger p ON t.passenger_id = p.passenger_id
        JOIN Station s ON t.station_id = s.station_id
        """
        
        where_clauses = []
        params = []
        
        # 添加筛选条件
        if hasattr(self, 'turnstile_passenger_id') and self.turnstile_passenger_id.get().strip():
            try:
                passenger_id = int(self.turnstile_passenger_id.get().strip())
                where_clauses.append("t.passenger_id = %s")
                params.append(passenger_id)
            except ValueError:
                messagebox.showwarning("输入错误", "乘客ID必须是一个有效的数字")
        
        if hasattr(self, 'turnstile_station_combobox') and \
           self.turnstile_station_combobox.get() != "全部站点" and \
           self.turnstile_station_combobox.get() in self.turnstile_station_data:
            station_id = self.turnstile_station_data[self.turnstile_station_combobox.get()]
            where_clauses.append("t.station_id = %s")
            params.append(station_id)
        
        # 组合查询
        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)
        
        base_query += " ORDER BY t.timestamp DESC LIMIT 100"
        
        # 执行查询
        logs = fetch_data(base_query, tuple(params))
        
        if logs:
            for idx, tl in enumerate(logs):
                row_visual_tag = 'oddrow.Treeview' if idx % 2 != 0 else ()
                tags_to_apply = (row_visual_tag,) if row_visual_tag else ()
                
                action_display = "进站" if tl['action'] == 'IN' else "出站"
                
                self.turnstile_tree.insert('', tk.END, values=(
                    tl['log_id'],
                    tl['passenger_id'],
                    tl['passenger_name'],
                    tl['station_name'],
                    action_display,
                    tl['formatted_time'],
                    tl['ticket_id'] if tl['ticket_id'] else '--'
                ), tags=tags_to_apply)
        else:
            self.turnstile_tree.insert('', tk.END, values=('--', '--', '无闸机记录', '', '', '', '--'))

    # --- Tab 4: Train Management (Mostly unchanged) ---
    def create_train_admin_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="列车管理 (管理员)")

        # Main PanedWindow for List and Form
        main_train_pane = ttk.PanedWindow(tab, orient=tk.VERTICAL)
        main_train_pane.pack(pady=10, padx=10, fill="both", expand=True) # Standard outer padding

        # --- Top Pane: Train List ---
        list_frame_outer = ttk.Frame(main_train_pane) # Frame to hold list and refresh
        main_train_pane.add(list_frame_outer, weight=3)

        list_frame = ttk.LabelFrame(list_frame_outer, text="列车列表")
        list_frame.pack(pady=5, padx=5, fill="both", expand=True) # Standard internal frame padding

        cols_train = ('train_id', 'train_number', 'line_name', 'model', 'capacity', 'status')
        self.train_admin_tree = ttk.Treeview(list_frame, columns=cols_train, show='headings', height=8, selectmode="browse")
        self.train_admin_tree.heading('train_id', text='ID')
        self.train_admin_tree.heading('train_number', text='列车编号')
        self.train_admin_tree.heading('line_name', text='所属线路')
        self.train_admin_tree.heading('model', text='型号')
        self.train_admin_tree.heading('capacity', text='容量')
        self.train_admin_tree.heading('status', text='状态')
        self.train_admin_tree.column('train_id', width=50, anchor=tk.CENTER, stretch=tk.NO)
        self.train_admin_tree.column('train_number', width=120)
        self.train_admin_tree.column('line_name', width=150)
        self.train_admin_tree.column('model', width=100)
        self.train_admin_tree.column('capacity', width=80, anchor=tk.E)
        self.train_admin_tree.column('status', width=100, anchor=tk.CENTER)


        scrollbar_train = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.train_admin_tree.yview)
        self.train_admin_tree.configure(yscroll=scrollbar_train.set)
        scrollbar_train.pack(side=tk.RIGHT, fill=tk.Y)
        self.train_admin_tree.pack(side=tk.LEFT, fill="both", expand=True)
        self.train_admin_tree.bind('<<TreeviewSelect>>', self.on_train_select)

        refresh_button_list = ttk.Button(list_frame_outer, text="刷新列表", command=self.load_trains)
        refresh_button_list.pack(side=tk.TOP, pady=5, padx=5, anchor='w') # Added padx=5


        # --- Bottom Pane: Add/Edit Train Form ---
        form_outer_frame = ttk.Frame(main_train_pane)
        main_train_pane.add(form_outer_frame, weight=2) # Give less weight initially

        form_frame = ttk.LabelFrame(form_outer_frame, text="添加/编辑列车信息")
        form_frame.pack(pady=5, padx=5, fill="both", expand=True) # Changed pady to 5

        # Form fields
        ttk.Label(form_frame, text="列车ID:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.train_form_id_label = ttk.Label(form_frame, text="自动生成") # Or display selected ID
        self.train_form_id_label.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(form_frame, text="列车编号:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.train_form_number_entry = ttk.Entry(form_frame, width=30)
        self.train_form_number_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(form_frame, text="所属线路:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.train_form_line_combobox = ttk.Combobox(form_frame, state="readonly", width=28)
        self.train_form_line_combobox.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        # self.load_lines_for_train_form() # Call this after form elements are created

        ttk.Label(form_frame, text="型号:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.train_form_model_entry = ttk.Entry(form_frame, width=30)
        self.train_form_model_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(form_frame, text="容量:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.train_form_capacity_entry = ttk.Entry(form_frame, width=15)
        self.train_form_capacity_entry.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(form_frame, text="状态:").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        self.train_form_status_combobox = ttk.Combobox(form_frame, values=['运行中', '维修中'], state="readonly", width=15)
        self.train_form_status_combobox.grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)

        # Action Buttons for the form
        form_button_frame = ttk.Frame(form_frame)
        form_button_frame.grid(row=6, column=0, columnspan=3, pady=10)

        self.train_form_add_button = ttk.Button(form_button_frame, text="添加新列车", command=self.add_train_action)
        self.train_form_add_button.pack(side=tk.LEFT, padx=5)

        self.train_form_save_button = ttk.Button(form_button_frame, text="保存更改", command=self.update_train_action, state=tk.DISABLED)
        self.train_form_save_button.pack(side=tk.LEFT, padx=5)

        self.train_form_delete_button = ttk.Button(form_button_frame, text="删除选中", command=self.delete_train_action, state=tk.DISABLED)
        self.train_form_delete_button.pack(side=tk.LEFT, padx=5)
        
        self.train_form_clear_button = ttk.Button(form_button_frame, text="清空表单", command=self.clear_train_form_action)
        self.train_form_clear_button.pack(side=tk.LEFT, padx=5)
        
        # Load initial data for list and form combobox
        self.load_lines_for_train_form() # Must be called after self.train_form_line_combobox is created
        self.load_trains() # This will also clear the form via its own call to clear_train_form_action

    def load_lines_for_train_form(self):
        """Load lines into the train form's line combobox."""
        if not hasattr(self, 'train_form_line_combobox'):
            return # Form not ready
        lines = fetch_data("SELECT line_id, line_name FROM Line WHERE status = '运营' ORDER BY line_name")
        self.train_form_line_data.clear() # Clear previous mapping
        line_names = []
        if lines:
            for line in lines:
                line_names.append(line['line_name'])
                self.train_form_line_data[line['line_name']] = line['line_id']
            self.train_form_line_combobox['values'] = line_names
            if line_names:
                self.train_form_line_combobox.current(0)
        else:
            self.train_form_line_combobox['values'] = []
            self.train_form_line_combobox.set("无可用线路")

    def populate_train_form(self, train_data):
        """Populate the form fields with data from the selected train."""
        self.train_form_id_label.config(text=str(train_data.get('train_id', '')))
        self.train_form_number_entry.delete(0, tk.END)
        self.train_form_number_entry.insert(0, train_data.get('train_number', ''))
        
        # Set line combobox
        line_name_to_select = train_data.get('line_name', '')
        if line_name_to_select and line_name_to_select in self.train_form_line_combobox['values']:
            self.train_form_line_combobox.set(line_name_to_select)
        elif self.train_form_line_combobox['values']: # has values but not the specific one
             self.train_form_line_combobox.current(0) # default to first if not found
        else: # no values in combobox
            self.train_form_line_combobox.set('')


        self.train_form_model_entry.delete(0, tk.END)
        self.train_form_model_entry.insert(0, train_data.get('model', ''))
        self.train_form_capacity_entry.delete(0, tk.END)
        self.train_form_capacity_entry.insert(0, str(train_data.get('capacity', '')))
        
        status_to_select = train_data.get('status', '')
        if status_to_select in self.train_form_status_combobox['values']:
             self.train_form_status_combobox.set(status_to_select)
        else:
            self.train_form_status_combobox.set('') # Clear if status not in list

    def clear_train_form_action(self, event=None):
        """Clear the train form and reset button states."""
        self.train_form_id_label.config(text="自动生成")
        if hasattr(self, 'train_form_number_entry'): self.train_form_number_entry.delete(0, tk.END)
        if hasattr(self, 'train_form_line_combobox') and self.train_form_line_combobox['values']:
            self.train_form_line_combobox.current(0)
        elif hasattr(self, 'train_form_line_combobox'):
            self.train_form_line_combobox.set('')
        if hasattr(self, 'train_form_model_entry'): self.train_form_model_entry.delete(0, tk.END)
        if hasattr(self, 'train_form_capacity_entry'): self.train_form_capacity_entry.delete(0, tk.END)
        if hasattr(self, 'train_form_status_combobox') and self.train_form_status_combobox['values']:
             self.train_form_status_combobox.current(0) # Default to '运营' or first item
        elif hasattr(self, 'train_form_status_combobox'):
            self.train_form_status_combobox.set('')


        if hasattr(self, 'train_admin_tree'): self.train_admin_tree.selection_remove(self.train_admin_tree.selection()) # Deselect

        if hasattr(self, 'train_form_add_button'): self.train_form_add_button.config(state=tk.NORMAL)
        if hasattr(self, 'train_form_save_button'): self.train_form_save_button.config(state=tk.DISABLED)
        if hasattr(self, 'train_form_delete_button'): self.train_form_delete_button.config(state=tk.DISABLED)
        # Keep selected_train_id_label for the old status update part (if still used)
        # if hasattr(self, 'selected_train_id_label'): self.selected_train_id_label.config(text="未选择")


    def add_train_action(self):
        train_number = self.train_form_number_entry.get()
        selected_line_name = self.train_form_line_combobox.get()
        model = self.train_form_model_entry.get()
        capacity_str = self.train_form_capacity_entry.get()
        status = self.train_form_status_combobox.get()

        if not all([train_number, selected_line_name, model, capacity_str, status]):
            messagebox.showwarning("输入不完整", "请填写所有列车信息。")
            return
        
        if selected_line_name == "无可用线路" or not selected_line_name:
             messagebox.showwarning("选择无效", "请选择一个有效的所属线路。")
             return

        line_id = self.train_form_line_data.get(selected_line_name)
        if not line_id:
            messagebox.showerror("错误", "无法找到所选线路的ID。")
            return

        try:
            capacity = int(capacity_str)
            if capacity <= 0: raise ValueError("Capacity must be positive")
        except ValueError:
            messagebox.showerror("输入错误", "容量必须是一个正整数。")
            return

        query = """
            INSERT INTO Train (train_number, line_id, model, capacity, status)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (train_number, line_id, model, capacity, status)
        new_train_id = execute_query(query, params)

        if new_train_id is not None:
            messagebox.showinfo("成功", f"新列车 '{train_number}' 添加成功，ID: {new_train_id}")
            self.load_trains() # Refreshes list and clears form
        # else: execute_query would have shown an error

    def update_train_action(self):
        selected_items = self.train_admin_tree.selection()
        if not selected_items:
            messagebox.showwarning("未选择", "请先在列表中选择一辆列车进行编辑。")
            return
        
        train_id_str = self.train_form_id_label.cget("text")
        if not train_id_str or train_id_str == "自动生成":
            messagebox.showerror("错误", "无法获取选中列车的ID进行更新。")
            return
        
        try:
            train_id = int(train_id_str)
        except ValueError:
            messagebox.showerror("错误", "选中的列车ID无效。")
            return

        train_number = self.train_form_number_entry.get()
        selected_line_name = self.train_form_line_combobox.get()
        model = self.train_form_model_entry.get()
        capacity_str = self.train_form_capacity_entry.get()
        status = self.train_form_status_combobox.get()

        if not all([train_number, selected_line_name, model, capacity_str, status]):
            messagebox.showwarning("输入不完整", "请填写所有列车信息进行更新。")
            return
        
        if selected_line_name == "无可用线路" or not selected_line_name:
             messagebox.showwarning("选择无效", "请选择一个有效的所属线路。")
             return

        line_id = self.train_form_line_data.get(selected_line_name)
        if not line_id:
            messagebox.showerror("错误", "无法找到所选线路的ID。")
            return
        
        try:
            capacity = int(capacity_str)
            if capacity <= 0: raise ValueError("Capacity must be positive")
        except ValueError:
            messagebox.showerror("输入错误", "容量必须是一个正整数。")
            return

        query = """
            UPDATE Train SET train_number = %s, line_id = %s, model = %s, capacity = %s, status = %s
            WHERE train_id = %s
        """
        params = (train_number, line_id, model, capacity, status, train_id)
        
        # execute_query for UPDATE might return None or rowcount depending on connector version/config
        # We'll check if it's not None, assuming an error would have shown a messagebox
        result = execute_query(query, params)
        
        # For robust check, ideally, we'd see if cursor.rowcount > 0
        # But for now, assume execute_query shows errors, and success means it didn't raise one.
        # if result is not None: # This condition might be too strict or too loose.
        messagebox.showinfo("成功", f"列车 ID {train_id} 的信息已更新。")
        self.load_trains() # Refreshes list and clears form
        # The 'else' for an error case is handled by execute_query showing a messagebox

    def delete_train_action(self):
        selected_items = self.train_admin_tree.selection()
        if not selected_items:
            messagebox.showwarning("未选择", "请先在列表中选择一辆列车进行删除。")
            return

        item = self.train_admin_tree.item(selected_items[0])
        train_id = item['values'][0]
        train_number = item['values'][1]

        confirm = messagebox.askyesno("确认删除", f"确定要删除列车 '{train_number}' (ID: {train_id}) 吗？\n此操作不可恢复！")
        if confirm:
            # Check for dependencies (e.g., in Schedule, TrainLog) before deleting.
            # For simplicity, this example doesn't implement cascading deletes or detailed dependency checks here.
            # Assume ON DELETE SET NULL or RESTRICT might be on related tables.
            
            # First, attempt to delete from TrainLog if it exists and has a foreign key
            # This is a placeholder for actual dependency management
            # execute_query("DELETE FROM TrainLog WHERE train_id = %s", (train_id,)) 
            # execute_query("DELETE FROM Schedule WHERE train_id = %s", (train_id,))

            query = "DELETE FROM Train WHERE train_id = %s"
            execute_query(query, (train_id,))
            
            # Similar to update, checking result's exact value is tricky.
            # Assume success if no error messagebox was shown by execute_query.
            messagebox.showinfo("成功", f"列车 '{train_number}' (ID: {train_id}) 已删除。")
            self.load_trains() # Refreshes list and clears form
            # The 'else' for an error case is handled by execute_query showing a messagebox

    def load_trains(self):
        """Load all train info into the admin Treeview and clear form."""
        if not hasattr(self, 'train_admin_tree'): # or other necessary form elements
            return

        for i in self.train_admin_tree.get_children():
            self.train_admin_tree.delete(i)
        
        # Clear form and reset buttons BEFORE loading new data that might trigger on_train_select
        # if hasattr(self, 'clear_train_form_action'): # Check if method exists
        #    self.clear_train_form_action() 

        query = "SELECT t.train_id, t.train_number, l.line_name, t.model, t.capacity, t.status FROM Train t JOIN Line l ON t.line_id = l.line_id ORDER BY t.train_id"
        trains = fetch_data(query)
        if trains:
            for idx, train in enumerate(trains):
                row_visual_tag = 'oddrow.Treeview' if idx % 2 != 0 else ()
                tags_to_apply = (row_visual_tag,) if row_visual_tag else ()
                self.train_admin_tree.insert('', tk.END, values=(train['train_id'], train['train_number'], train['line_name'], train['model'] if train['model'] else 'N/A', train['capacity'] if train['capacity'] else 'N/A', train['status']), tags=tags_to_apply)
        
        # Call clear_train_form_action AFTER list is populated and selections might be cleared
        if hasattr(self, 'clear_train_form_action'): # Ensure method exists
           self.clear_train_form_action()


    def on_train_select(self, event=None):
        """Called when a train is selected. Populates form and manages button states."""
        # Ensure all form widgets and necessary attributes exist
        if not all(hasattr(self, attr) for attr in [
            'train_admin_tree', 'train_form_id_label', 'train_form_number_entry',
            'train_form_line_combobox', 'train_form_model_entry', 'train_form_capacity_entry',
            'train_form_status_combobox', 'train_form_add_button', 'train_form_save_button',
            'train_form_delete_button'
        ]):
            return # Form not fully initialized

        selected_items = self.train_admin_tree.selection()
        if selected_items:
            item = self.train_admin_tree.item(selected_items[0])
            values = item['values']
            train_data_dict = {
                'train_id': values[0],
                'train_number': values[1],
                'line_name': values[2], # We need line_name to set combobox
                'model': values[3],
                'capacity': values[4],
                'status': values[5]
            }
            self.populate_train_form(train_data_dict)
            self.train_form_add_button.config(state=tk.DISABLED)
            self.train_form_save_button.config(state=tk.NORMAL)
            self.train_form_delete_button.config(state=tk.NORMAL)
            
            # Old status update logic (can be removed or kept if separate quick update is desired)
            # self.selected_train_id_label.config(text=str(values[0]))
            # if values[5] in self.new_status_combobox['values']:
            #    self.new_status_combobox.set(values[5])
            # else:
            #    self.new_status_combobox.set('')
        else:
            # No selection, so clear form and reset buttons for "add" mode
            self.clear_train_form_action() 
            # self.selected_train_id_label.config(text="未选择")
            # self.new_status_combobox.set('')


    # def update_train_status(self): # This method might be redundant now or can be kept for quick status only update
    # ... (existing update_train_status code, which only updated status) ...

    # ... (rest of the class methods) ...

    def create_staff_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="员工与排班管理")

        main_staff_pane = ttk.PanedWindow(tab, orient=tk.VERTICAL)
        main_staff_pane.pack(pady=10, padx=10, fill="both", expand=True)

        # --- Top Pane: Staff Management (List and Form) ---
        staff_management_frame = ttk.Frame(main_staff_pane)
        main_staff_pane.add(staff_management_frame, weight=2) # Adjusted weight

        staff_list_form_pane = ttk.PanedWindow(staff_management_frame, orient=tk.HORIZONTAL)
        staff_list_form_pane.pack(fill="both", expand=True)

        staff_list_outer_frame = ttk.Frame(staff_list_form_pane)
        staff_list_form_pane.add(staff_list_outer_frame, weight=2)

        staff_frame = ttk.LabelFrame(staff_list_outer_frame, text="员工列表")
        staff_frame.pack(pady=5, padx=5, fill="both", expand=True)
        cols_s = ('staff_id', 'name', 'role', 'contact', 'hire_date', 'status')
        self.staff_tree = ttk.Treeview(staff_frame, columns=cols_s, show='headings', height=6, selectmode="browse") # Reduced height
        header_texts_s = ['ID', '姓名', '岗位', '联系方式', '入职日期', '状态']
        col_widths_s = [40, 100, 100, 120, 100, 80]
        for c, h, w in zip(cols_s, header_texts_s, col_widths_s):
            self.staff_tree.heading(c, text=h)
            self.staff_tree.column(c, width=w, minwidth=w, anchor=tk.W)
        staff_scrollbar = ttk.Scrollbar(staff_frame, orient=tk.VERTICAL, command=self.staff_tree.yview)
        self.staff_tree.configure(yscroll=staff_scrollbar.set)
        staff_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.staff_tree.pack(side=tk.LEFT, fill="both", expand=True)
        self.staff_tree.bind('<<TreeviewSelect>>', self.on_staff_select)
        refresh_staff_button = ttk.Button(staff_list_outer_frame, text="刷新员工列表", command=self.load_staff_data)
        refresh_staff_button.pack(pady=5, anchor='w', padx=5)

        staff_form_outer_frame = ttk.Frame(staff_list_form_pane)
        staff_list_form_pane.add(staff_form_outer_frame, weight=3)
        staff_edit_frame = ttk.LabelFrame(staff_form_outer_frame, text="添加/编辑员工信息")
        staff_edit_frame.pack(pady=5, padx=5, fill="both", expand=True)
        ttk.Label(staff_edit_frame, text="员工ID:").grid(row=0, column=0, padx=5, pady=3, sticky=tk.W)
        self.staff_form_widgets['id_label'] = ttk.Label(staff_edit_frame, text="自动生成")
        self.staff_form_widgets['id_label'].grid(row=0, column=1, padx=5, pady=3, sticky=tk.W)
        ttk.Label(staff_edit_frame, text="姓名:").grid(row=1, column=0, padx=5, pady=3, sticky=tk.W)
        self.staff_form_widgets['name_entry'] = ttk.Entry(staff_edit_frame, width=30)
        self.staff_form_widgets['name_entry'].grid(row=1, column=1, padx=5, pady=3, sticky=tk.W)
        ttk.Label(staff_edit_frame, text="岗位:").grid(row=2, column=0, padx=5, pady=3, sticky=tk.W)
        self.staff_form_widgets['role_combobox'] = ttk.Combobox(staff_edit_frame, values=self.staff_roles, state="readonly", width=28)
        self.staff_form_widgets['role_combobox'].grid(row=2, column=1, padx=5, pady=3, sticky=tk.W)
        ttk.Label(staff_edit_frame, text="联系方式:").grid(row=3, column=0, padx=5, pady=3, sticky=tk.W)
        self.staff_form_widgets['contact_entry'] = ttk.Entry(staff_edit_frame, width=30)
        self.staff_form_widgets['contact_entry'].grid(row=3, column=1, padx=5, pady=3, sticky=tk.W)
        ttk.Label(staff_edit_frame, text="入职日期:").grid(row=4, column=0, padx=5, pady=3, sticky=tk.W)
        self.staff_form_widgets['hire_date_entry'] = ttk.Entry(staff_edit_frame, width=15)
        self.staff_form_widgets['hire_date_entry'].grid(row=4, column=1, padx=5, pady=3, sticky=tk.W)
        ttk.Label(staff_edit_frame, text="(YYYY-MM-DD)").grid(row=4, column=2, padx=2, pady=3, sticky=tk.W)
        ttk.Label(staff_edit_frame, text="状态:").grid(row=5, column=0, padx=5, pady=3, sticky=tk.W)
        self.staff_form_widgets['status_combobox'] = ttk.Combobox(staff_edit_frame, values=self.staff_statuses, state="readonly", width=15)
        self.staff_form_widgets['status_combobox'].grid(row=5, column=1, padx=5, pady=3, sticky=tk.W)
        staff_form_button_frame = ttk.Frame(staff_edit_frame)
        staff_form_button_frame.grid(row=6, column=0, columnspan=3, pady=10)
        self.staff_form_widgets['add_button'] = ttk.Button(staff_form_button_frame, text="添加新员工", command=self.add_staff_action)
        self.staff_form_widgets['add_button'].pack(side=tk.LEFT, padx=5)
        self.staff_form_widgets['save_button'] = ttk.Button(staff_form_button_frame, text="保存更改", command=self.update_staff_action, state=tk.DISABLED)
        self.staff_form_widgets['save_button'].pack(side=tk.LEFT, padx=5)
        self.staff_form_widgets['delete_button'] = ttk.Button(staff_form_button_frame, text="删除选中", command=self.delete_staff_action, state=tk.DISABLED)
        self.staff_form_widgets['delete_button'].pack(side=tk.LEFT, padx=5)
        self.staff_form_widgets['clear_button'] = ttk.Button(staff_form_button_frame, text="清空表单", command=self.clear_staff_form_action)
        self.staff_form_widgets['clear_button'].pack(side=tk.LEFT, padx=5)


        # --- Bottom Pane: Assignment Management (List and Form) ---
        assignment_management_frame = ttk.Frame(main_staff_pane)
        main_staff_pane.add(assignment_management_frame, weight=3) # Adjusted weight

        # Assignment List Frame (Top part of assignment_management_frame)
        assign_list_frame = ttk.LabelFrame(assignment_management_frame, text="排班记录列表")
        assign_list_frame.pack(pady=5, padx=5, fill="both", expand=True) # Standard internal

        cols_a = ('assign_id', 'staff_name', 'station_name', 'start_time', 'end_time', 'shift_type')
        self.assign_tree = ttk.Treeview(assign_list_frame, columns=cols_a, show='headings', height=6, selectmode="browse") # Reduced height
        header_texts_a = ['排班ID', '员工姓名', '站点名称', '开始时间', '结束时间', '班次类型']
        col_widths_a = [60, 100, 120, 140, 140, 80]
        for c, h, w in zip(cols_a, header_texts_a, col_widths_a):
            self.assign_tree.heading(c, text=h)
            self.assign_tree.column(c, width=w, minwidth=w, anchor=tk.W)
        assign_scrollbar = ttk.Scrollbar(assign_list_frame, orient=tk.VERTICAL, command=self.assign_tree.yview)
        self.assign_tree.configure(yscroll=assign_scrollbar.set)
        assign_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.assign_tree.pack(side=tk.LEFT, fill="both", expand=True)
        self.assign_tree.bind('<<TreeviewSelect>>', self.on_assignment_select)

        refresh_assign_button = ttk.Button(assign_list_frame, text="刷新排班列表", command=self.load_assignment_data)
        refresh_assign_button.pack(pady=5, padx=5, anchor='w', side=tk.BOTTOM) # Added padx=5

        # Assignment Form Frame (Bottom part of assignment_management_frame)
        assign_edit_frame = ttk.LabelFrame(assignment_management_frame, text="添加/编辑排班记录")
        assign_edit_frame.pack(pady=5, padx=5, fill="x", expand=False) # Changed pady to 5
        # ... (assign form fields with grid padx=5, pady=3 - dense form, kept as is) ...
        ttk.Label(assign_edit_frame, text="排班ID:").grid(row=0, column=0, padx=5, pady=3, sticky=tk.W)
        self.assignment_form_widgets['id_label'] = ttk.Label(assign_edit_frame, text="自动生成")
        self.assignment_form_widgets['id_label'].grid(row=0, column=1, padx=5, pady=3, sticky=tk.W)
        ttk.Label(assign_edit_frame, text="员工:").grid(row=1, column=0, padx=5, pady=3, sticky=tk.W)
        self.assignment_form_widgets['staff_combobox'] = ttk.Combobox(assign_edit_frame, state="readonly", width=28)
        self.assignment_form_widgets['staff_combobox'].grid(row=1, column=1, padx=5, pady=3, sticky=tk.W)
        ttk.Label(assign_edit_frame, text="站点:").grid(row=2, column=0, padx=5, pady=3, sticky=tk.W)
        self.assignment_form_widgets['station_combobox'] = ttk.Combobox(assign_edit_frame, state="readonly", width=28)
        self.assignment_form_widgets['station_combobox'].grid(row=2, column=1, padx=5, pady=3, sticky=tk.W)
        ttk.Label(assign_edit_frame, text="开始时间:").grid(row=3, column=0, padx=5, pady=3, sticky=tk.W)
        self.assignment_form_widgets['start_time_entry'] = ttk.Entry(assign_edit_frame, width=30)
        self.assignment_form_widgets['start_time_entry'].grid(row=3, column=1, padx=5, pady=3, sticky=tk.W)
        ttk.Label(assign_edit_frame, text="(YYYY-MM-DD HH:MM:SS)").grid(row=3, column=2, padx=2, pady=3, sticky=tk.W)
        ttk.Label(assign_edit_frame, text="结束时间:").grid(row=4, column=0, padx=5, pady=3, sticky=tk.W)
        self.assignment_form_widgets['end_time_entry'] = ttk.Entry(assign_edit_frame, width=30)
        self.assignment_form_widgets['end_time_entry'].grid(row=4, column=1, padx=5, pady=3, sticky=tk.W)
        ttk.Label(assign_edit_frame, text="(YYYY-MM-DD HH:MM:SS)").grid(row=4, column=2, padx=2, pady=3, sticky=tk.W)
        ttk.Label(assign_edit_frame, text="班次类型:").grid(row=5, column=0, padx=5, pady=3, sticky=tk.W)
        self.assignment_form_widgets['shift_type_combobox'] = ttk.Combobox(assign_edit_frame, values=self.shift_types, state="readonly", width=28)
        self.assignment_form_widgets['shift_type_combobox'].grid(row=5, column=1, padx=5, pady=3, sticky=tk.W)
        assign_form_button_frame = ttk.Frame(assign_edit_frame)
        assign_form_button_frame.grid(row=6, column=0, columnspan=3, pady=10)
        self.assignment_form_widgets['add_button'] = ttk.Button(assign_form_button_frame, text="添加新排班", command=self.add_assignment_action)
        self.assignment_form_widgets['add_button'].pack(side=tk.LEFT, padx=5)
        self.assignment_form_widgets['save_button'] = ttk.Button(assign_form_button_frame, text="保存更改", command=self.update_assignment_action, state=tk.DISABLED)
        self.assignment_form_widgets['save_button'].pack(side=tk.LEFT, padx=5)
        self.assignment_form_widgets['delete_button'] = ttk.Button(assign_form_button_frame, text="删除选中", command=self.delete_assignment_action, state=tk.DISABLED)
        self.assignment_form_widgets['delete_button'].pack(side=tk.LEFT, padx=5)
        self.assignment_form_widgets['clear_button'] = ttk.Button(assign_form_button_frame, text="清空表单", command=self.clear_assignment_form_action)
        self.assignment_form_widgets['clear_button'].pack(side=tk.LEFT, padx=5)

        # Load initial data for staff, assignments, and form comboboxes
        self.load_staff_data()
        self.load_assignment_data()
        self.load_staff_for_assignment_form()
        self.load_stations_for_assignment_form()

    def load_staff_for_assignment_form(self):
        if not hasattr(self.assignment_form_widgets, 'get') or not self.assignment_form_widgets.get('staff_combobox'): return
        staff_on_duty = fetch_data("SELECT staff_id, name FROM Staff WHERE status = '在职' ORDER BY name")
        self.assignment_staff_data.clear()
        staff_names = []
        if staff_on_duty:
            for s in staff_on_duty:
                staff_names.append(s['name'])
                self.assignment_staff_data[s['name']] = s['staff_id']
            self.assignment_form_widgets['staff_combobox']['values'] = staff_names
            if staff_names: self.assignment_form_widgets['staff_combobox'].current(0)
        else:
            self.assignment_form_widgets['staff_combobox']['values'] = []
            self.assignment_form_widgets['staff_combobox'].set("无在职员工")
            
    def load_stations_for_assignment_form(self):
        if not hasattr(self.assignment_form_widgets, 'get') or not self.assignment_form_widgets.get('station_combobox'): return
        stations = fetch_data("SELECT station_id, station_name FROM Station ORDER BY station_name")
        self.assignment_station_data.clear()
        station_names = []
        if stations:
            for st in stations:
                station_names.append(st['station_name'])
                self.assignment_station_data[st['station_name']] = st['station_id']
            self.assignment_form_widgets['station_combobox']['values'] = station_names
            if station_names: self.assignment_form_widgets['station_combobox'].current(0)
        else:
            self.assignment_form_widgets['station_combobox']['values'] = []
            self.assignment_form_widgets['station_combobox'].set("无可用站点")

    def load_staff_data(self):
        """Load staff data into the staff_tree and clear the form."""
        if not hasattr(self, 'staff_tree'): return
        for i in self.staff_tree.get_children():
            self.staff_tree.delete(i)
        
        staff_list = fetch_data("SELECT staff_id, name, role, contact, DATE_FORMAT(hire_date, '%Y-%m-%d') as hire_date, status FROM Staff ORDER BY staff_id")
        if staff_list:
            for idx, s in enumerate(staff_list):
                row_visual_tag = 'oddrow.Treeview' if idx % 2 != 0 else ()
                tags_to_apply = (row_visual_tag,) if row_visual_tag else ()
                self.staff_tree.insert('', tk.END, values=(s.get('staff_id'), s.get('name'), s.get('role'), s.get('contact'), s.get('hire_date', ''), s.get('status')), tags=tags_to_apply)
        if hasattr(self, 'clear_staff_form_action'): # Check if clear_staff_form_action is defined
            self.clear_staff_form_action()
        # Refresh staff for assignment form as well, in case of status changes etc.
        if hasattr(self, 'load_staff_for_assignment_form'): self.load_staff_for_assignment_form()

    def load_assignment_data(self):
        """Load assignment data into the assign_tree."""
        if not hasattr(self, 'assign_tree'): return
        for i in self.assign_tree.get_children():
            self.assign_tree.delete(i)
        query = "SELECT sa.assign_id, s.name AS staff_name, st.station_name, DATE_FORMAT(sa.start_time, '%Y-%m-%d %H:%M:%S') as start_time, DATE_FORMAT(sa.end_time, '%Y-%m-%d %H:%M:%S') as end_time, sa.shift_type FROM StaffAssignment sa JOIN Staff s ON sa.staff_id = s.staff_id JOIN Station st ON sa.station_id = st.station_id ORDER BY sa.assign_id DESC"
        assignments = fetch_data(query)
        if assignments:
            for idx, a in enumerate(assignments):
                row_visual_tag = 'oddrow.Treeview' if idx % 2 != 0 else ()
                tags_to_apply = (row_visual_tag,) if row_visual_tag else ()
                self.assign_tree.insert('', tk.END, values=(a.get('assign_id'), a.get('staff_name'), a.get('station_name'),a.get('start_time'), a.get('end_time'), a.get('shift_type', 'N/A')), tags=tags_to_apply)
        if hasattr(self, 'clear_assignment_form_action'): 
            self.clear_assignment_form_action()

    def on_staff_select(self, event=None):
        if not all(hasattr(self.staff_form_widgets.get(key), 'cget') for key in ['add_button', 'save_button', 'delete_button'] ):
            return # Form widgets not ready

        selected_items = self.staff_tree.selection()
        if selected_items:
            item = self.staff_tree.item(selected_items[0])
            values = item['values']
            staff_data_dict = {
                'staff_id': values[0],
                'name': values[1],
                'role': values[2],
                'contact': values[3],
                'hire_date': values[4],
                'status': values[5]
            }
            self.populate_staff_form(staff_data_dict)
            self.staff_form_widgets['add_button'].config(state=tk.DISABLED)
            self.staff_form_widgets['save_button'].config(state=tk.NORMAL)
            self.staff_form_widgets['delete_button'].config(state=tk.NORMAL)
        else:
            self.clear_staff_form_action()

    def populate_staff_form(self, data):
        self.staff_form_widgets['id_label'].config(text=str(data.get('staff_id', '自动生成')))
        self.staff_form_widgets['name_entry'].delete(0, tk.END)
        self.staff_form_widgets['name_entry'].insert(0, data.get('name', ''))
        self.staff_form_widgets['role_combobox'].set(data.get('role', ''))
        self.staff_form_widgets['contact_entry'].delete(0, tk.END)
        self.staff_form_widgets['contact_entry'].insert(0, data.get('contact', ''))
        self.staff_form_widgets['hire_date_entry'].delete(0, tk.END)
        self.staff_form_widgets['hire_date_entry'].insert(0, data.get('hire_date', ''))
        self.staff_form_widgets['status_combobox'].set(data.get('status', ''))
        
        # Ensure comboboxes show a value even if data.get('X') is not in current values list
        if data.get('role', '') not in self.staff_form_widgets['role_combobox']['values'] and self.staff_form_widgets['role_combobox']['values']:
            self.staff_form_widgets['role_combobox'].current(0)
        if data.get('status', '') not in self.staff_form_widgets['status_combobox']['values'] and self.staff_form_widgets['status_combobox']['values']:
            self.staff_form_widgets['status_combobox'].current(0)

    def clear_staff_form_action(self, event=None):
        if not self.staff_form_widgets: return # Form not ready
        self.staff_form_widgets['id_label'].config(text="自动生成")
        for key in ['name_entry', 'contact_entry', 'hire_date_entry']:
            if self.staff_form_widgets.get(key):
                 self.staff_form_widgets[key].delete(0, tk.END)
        if self.staff_form_widgets.get('role_combobox') and self.staff_form_widgets['role_combobox']['values']:
            self.staff_form_widgets['role_combobox'].current(0)
        if self.staff_form_widgets.get('status_combobox') and self.staff_form_widgets['status_combobox']['values']:
            self.staff_form_widgets['status_combobox'].current(0)

        if hasattr(self, 'staff_tree') and self.staff_tree.selection():
             self.staff_tree.selection_remove(self.staff_tree.selection())

        if self.staff_form_widgets.get('add_button'): self.staff_form_widgets['add_button'].config(state=tk.NORMAL)
        if self.staff_form_widgets.get('save_button'): self.staff_form_widgets['save_button'].config(state=tk.DISABLED)
        if self.staff_form_widgets.get('delete_button'): self.staff_form_widgets['delete_button'].config(state=tk.DISABLED)

    def add_staff_action(self):
        name = self.staff_form_widgets['name_entry'].get()
        role = self.staff_form_widgets['role_combobox'].get()
        contact = self.staff_form_widgets['contact_entry'].get()
        hire_date_str = self.staff_form_widgets['hire_date_entry'].get()
        status = self.staff_form_widgets['status_combobox'].get()

        if not all([name, role, contact, hire_date_str, status]):
            messagebox.showwarning("输入不完整", "请填写所有员工信息。")
            return
        try:
            datetime.strptime(hire_date_str, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("日期格式错误", "入职日期格式应为 YYYY-MM-DD。")
            return

        query = "INSERT INTO Staff (name, role, contact, hire_date, status) VALUES (%s, %s, %s, %s, %s)"
        params = (name, role, contact, hire_date_str, status)
        new_id = execute_query(query, params)
        if new_id is not None:
            messagebox.showinfo("成功", f"新员工 '{name}' 添加成功，ID: {new_id}")
            self.load_staff_data()

    def update_staff_action(self):
        staff_id_str = self.staff_form_widgets['id_label'].cget("text")
        if not staff_id_str or staff_id_str == "自动生成":
            messagebox.showerror("错误", "未选择有效的员工进行更新或ID丢失。")
            return
        try:
            staff_id = int(staff_id_str)
        except ValueError:
            messagebox.showerror("错误", "员工ID无效。")
            return

        name = self.staff_form_widgets['name_entry'].get()
        role = self.staff_form_widgets['role_combobox'].get()
        contact = self.staff_form_widgets['contact_entry'].get()
        hire_date_str = self.staff_form_widgets['hire_date_entry'].get()
        status = self.staff_form_widgets['status_combobox'].get()

        if not all([name, role, contact, hire_date_str, status]):
            messagebox.showwarning("输入不完整", "请填写所有员工信息进行更新。")
            return
        try:
            datetime.strptime(hire_date_str, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("日期格式错误", "入职日期格式应为 YYYY-MM-DD。")
            return

        query = "UPDATE Staff SET name=%s, role=%s, contact=%s, hire_date=%s, status=%s WHERE staff_id=%s"
        params = (name, role, contact, hire_date_str, status, staff_id)
        execute_query(query, params)
        # Assuming execute_query shows error if any, otherwise it's a success
        messagebox.showinfo("成功", f"员工 ID {staff_id} 的信息已更新。")
        self.load_staff_data()

    def delete_staff_action(self):
        staff_id_str = self.staff_form_widgets['id_label'].cget("text")
        name = self.staff_form_widgets['name_entry'].get() # Get name for confirm dialog
        if not staff_id_str or staff_id_str == "自动生成":
            messagebox.showerror("错误", "未选择有效的员工进行删除。")
            return
        try:
            staff_id = int(staff_id_str)
        except ValueError:
            messagebox.showerror("错误", "员工ID无效。")
            return

        confirm = messagebox.askyesno("确认删除", f"确定要删除员工 '{name}' (ID: {staff_id}) 吗？\n此操作可能会影响其排班记录 (如果数据库设置了级联删除或限制)。")
        if confirm:
            # Check for related records in StaffAssignment
            assignments = fetch_data("SELECT 1 FROM StaffAssignment WHERE staff_id = %s LIMIT 1", (staff_id,))
            if assignments:
                confirm_cascade = messagebox.askyesno("警告：存在关联数据", 
                    f"员工 '{name}' (ID: {staff_id}) 存在排班记录。\n\nMySQL数据库的默认外键行为 (ON DELETE RESTRICT) 会阻止删除此员工。\n如果外键设置为 ON DELETE CASCADE，排班记录将被一同删除。\n如果设置为 ON DELETE SET NULL，排班记录中的员工ID将变为空。\n\n是否仍要尝试删除此员工 (操作可能因数据库约束而失败)？")
                if not confirm_cascade:
                    return
            
            query = "DELETE FROM Staff WHERE staff_id = %s"
            execute_query(query, (staff_id,))
            # Assuming execute_query shows error if deletion fails due to FK constraints
            messagebox.showinfo("尝试删除", f"已尝试删除员工 '{name}' (ID: {staff_id})。请检查列表确认结果。")
            self.load_staff_data()

    # --- StaffAssignment CRUD methods ---
    def on_assignment_select(self, event=None):
        if not all(hasattr(self.assignment_form_widgets.get(key), 'cget') for key in ['add_button', 'save_button', 'delete_button']):
            return # Form not ready
        selected_items = self.assign_tree.selection()
        if selected_items:
            item = self.assign_tree.item(selected_items[0])
            values = item['values'] # ('assign_id', 'staff_name', 'station_name', 'start_time', 'end_time', 'shift_type')
            assignment_data = {
                'assign_id': values[0],
                'staff_name': values[1],
                'station_name': values[2],
                'start_time': values[3],
                'end_time': values[4],
                'shift_type': values[5]
            }
            self.populate_assignment_form(assignment_data)
            self.assignment_form_widgets['add_button'].config(state=tk.DISABLED)
            self.assignment_form_widgets['save_button'].config(state=tk.NORMAL)
            self.assignment_form_widgets['delete_button'].config(state=tk.NORMAL)
        else:
            self.clear_assignment_form_action()

    def populate_assignment_form(self, data):
        self.assignment_form_widgets['id_label'].config(text=str(data.get('assign_id', '自动生成')))
        self.assignment_form_widgets['staff_combobox'].set(data.get('staff_name', ''))
        self.assignment_form_widgets['station_combobox'].set(data.get('station_name', ''))
        self.assignment_form_widgets['start_time_entry'].delete(0, tk.END)
        self.assignment_form_widgets['start_time_entry'].insert(0, data.get('start_time', ''))
        self.assignment_form_widgets['end_time_entry'].delete(0, tk.END)
        self.assignment_form_widgets['end_time_entry'].insert(0, data.get('end_time', ''))
        self.assignment_form_widgets['shift_type_combobox'].set(data.get('shift_type', ''))
        # Ensure comboboxes show a valid selection even if the data isn't in the list (e.g. inactive staff)
        # For staff/station, if name not in current list, it will just show blank. This might be ok.

    def clear_assignment_form_action(self, event=None):
        if not self.assignment_form_widgets: return
        self.assignment_form_widgets['id_label'].config(text="自动生成")
        for key in ['start_time_entry', 'end_time_entry']:
            if self.assignment_form_widgets.get(key): self.assignment_form_widgets[key].delete(0, tk.END)
        
        if self.assignment_form_widgets.get('staff_combobox') and self.assignment_form_widgets['staff_combobox']['values']:
            self.assignment_form_widgets['staff_combobox'].current(0)
        if self.assignment_form_widgets.get('station_combobox') and self.assignment_form_widgets['station_combobox']['values']:
            self.assignment_form_widgets['station_combobox'].current(0)
        if self.assignment_form_widgets.get('shift_type_combobox') and self.assignment_form_widgets['shift_type_combobox']['values']:
            self.assignment_form_widgets['shift_type_combobox'].current(0)

        if hasattr(self, 'assign_tree') and self.assign_tree.selection():
            self.assign_tree.selection_remove(self.assign_tree.selection())

        if self.assignment_form_widgets.get('add_button'): self.assignment_form_widgets['add_button'].config(state=tk.NORMAL)
        if self.assignment_form_widgets.get('save_button'): self.assignment_form_widgets['save_button'].config(state=tk.DISABLED)
        if self.assignment_form_widgets.get('delete_button'): self.assignment_form_widgets['delete_button'].config(state=tk.DISABLED)

    def add_assignment_action(self):
        staff_name = self.assignment_form_widgets['staff_combobox'].get()
        station_name = self.assignment_form_widgets['station_combobox'].get()
        start_time_str = self.assignment_form_widgets['start_time_entry'].get()
        end_time_str = self.assignment_form_widgets['end_time_entry'].get()
        shift_type = self.assignment_form_widgets['shift_type_combobox'].get()

        if not all([staff_name, station_name, start_time_str, end_time_str, shift_type]) or \
           staff_name == "无在职员工" or station_name == "无可用站点":
            messagebox.showwarning("输入不完整", "请填写所有排班信息并确保选择了有效的员工和站点。")
            return
        
        staff_id = self.assignment_staff_data.get(staff_name)
        station_id = self.assignment_station_data.get(station_name)
        if not staff_id or not station_id:
            messagebox.showerror("选择错误", "无法匹配员工或站点ID。请确保列表已正确加载。")
            return
        try:
            datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
            datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            messagebox.showerror("日期格式错误", "开始/结束时间格式应为 YYYY-MM-DD HH:MM:SS。")
            return

        query = "INSERT INTO StaffAssignment (staff_id, station_id, start_time, end_time, shift_type) VALUES (%s, %s, %s, %s, %s)"
        params = (staff_id, station_id, start_time_str, end_time_str, shift_type)
        new_id = execute_query(query, params)
        if new_id is not None:
            messagebox.showinfo("成功", f"新排班记录添加成功，ID: {new_id}")
            self.load_assignment_data()

    def update_assignment_action(self):
        assign_id_str = self.assignment_form_widgets['id_label'].cget("text")
        if not assign_id_str or assign_id_str == "自动生成": messagebox.showerror("错误", "未选择有效的排班记录进行更新。"); return
        try: assign_id = int(assign_id_str)
        except ValueError: messagebox.showerror("错误", "排班ID无效。"); return

        staff_name = self.assignment_form_widgets['staff_combobox'].get()
        station_name = self.assignment_form_widgets['station_combobox'].get()
        start_time_str = self.assignment_form_widgets['start_time_entry'].get()
        end_time_str = self.assignment_form_widgets['end_time_entry'].get()
        shift_type = self.assignment_form_widgets['shift_type_combobox'].get()

        if not all([staff_name, station_name, start_time_str, end_time_str, shift_type]) or \
           staff_name == "无在职员工" or station_name == "无可用站点":
            messagebox.showwarning("输入不完整", "请填写所有排班信息并确保选择了有效的员工和站点。")
            return

        staff_id = self.assignment_staff_data.get(staff_name)
        station_id = self.assignment_station_data.get(station_name)
        if not staff_id or not station_id: messagebox.showerror("选择错误", "无法匹配员工或站点ID。请确保列表已正确加载。"); return
        try:
            datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
            datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
        except ValueError: messagebox.showerror("日期格式错误", "开始/结束时间格式应为 YYYY-MM-DD HH:MM:SS。"); return

        query = "UPDATE StaffAssignment SET staff_id=%s, station_id=%s, start_time=%s, end_time=%s, shift_type=%s WHERE assign_id=%s"
        params = (staff_id, station_id, start_time_str, end_time_str, shift_type, assign_id)
        execute_query(query, params)
        messagebox.showinfo("成功", f"排班记录 ID {assign_id} 的信息已更新。")
        self.load_assignment_data()

    def delete_assignment_action(self):
        assign_id_str = self.assignment_form_widgets['id_label'].cget("text")
        if not assign_id_str or assign_id_str == "自动生成": messagebox.showerror("错误", "未选择有效的排班记录进行删除。"); return
        try: assign_id = int(assign_id_str)
        except ValueError: messagebox.showerror("错误", "排班ID无效。"); return

        confirm = messagebox.askyesno("确认删除", f"确定要删除排班记录 ID: {assign_id} 吗？")
        if confirm:
            query = "DELETE FROM StaffAssignment WHERE assign_id = %s"
            execute_query(query, (assign_id,))
            messagebox.showinfo("成功", f"排班记录 ID {assign_id} 已删除。")
            self.load_assignment_data()

    # ... (other methods like create_maint_tab, etc.) ...

    def create_maint_tab(self):
        tab = ttk.Frame(self.notebook); self.notebook.add(tab, text="设备维保 (管理员)")
        m_frame = ttk.LabelFrame(tab, text="维护记录"); m_frame.pack(fill="both", expand=True, padx=10, pady=10) # Standard section padding
        cols_m = ('record_id', 'equipment_name', 'equipment_type', 'station_name', 'staff_name', 'start_time', 'end_time', 'description')
        self.maint_tree = ttk.Treeview(m_frame, columns=cols_m, show='headings', height=12)
        headers = ['记录ID', '设备名', '设备类型', '所在站点', '维修员工', '开始时间', '结束时间', '维护描述']; col_widths = [60, 150, 100, 120, 80, 150, 150, 200]
        for c, h, w in zip(cols_m, headers, col_widths): self.maint_tree.heading(c, text=h); self.maint_tree.column(c, width=w, anchor=tk.W)
        # Scrollbar for maint_tree
        maint_scrollbar = ttk.Scrollbar(m_frame, orient=tk.VERTICAL, command=self.maint_tree.yview)
        self.maint_tree.configure(yscrollcommand=maint_scrollbar.set)
        maint_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.maint_tree.pack(side=tk.LEFT, fill="both", expand=True)
        query = "SELECT mr.record_id, e.equipment_name, e.equipment_type, s_st.station_name, st_staff.name AS staff_name, mr.start_time, mr.end_time, mr.description FROM MaintenanceRecord mr JOIN Equipment e ON mr.equipment_id = e.equipment_id JOIN Station s_st ON mr.station_id = s_st.station_id LEFT JOIN Staff st_staff ON mr.staff_id = st_staff.staff_id ORDER BY mr.record_id DESC"
        records = fetch_data(query)
        if records:
            for idx, r in enumerate(records):
                values_tuple = (r.get('record_id', ''), r.get('equipment_name', ''), r.get('equipment_type', ''), r.get('station_name', ''), r.get('staff_name', 'N/A'), r.get('start_time', '').strftime('%Y-%m-%d %H:%M:%S') if r.get('start_time') else '', r.get('end_time', '').strftime('%Y-%m-%d %H:%M:%S') if r.get('end_time') else '进行中', r.get('description', ''))
                row_visual_tag = 'oddrow.Treeview' if idx % 2 != 0 else (); tags_to_apply = (row_visual_tag,) if row_visual_tag else ()
                self.maint_tree.insert('', tk.END, values=values_tuple, tags=tags_to_apply)
        else:
            self.maint_tree.insert('', tk.END, values=("无维保记录", "", "", "", "", "", "", ""))

    def create_alert_tab(self):
        tab = ttk.Frame(self.notebook); self.notebook.add(tab, text="服务公告")
        a_frame = ttk.LabelFrame(tab, text="公告列表"); a_frame.pack(fill="both", expand=True, padx=10, pady=10) # Standard section padding
        cols_al = ('alert_id','line_id','station_id','start_time','end_time','message'); self.alert_tree = ttk.Treeview(a_frame, columns=cols_al, show='headings', height=12)
        headers = ['ID','线路ID','站点ID','开始','结束','内容']
        for c,h in zip(cols_al, headers): self.alert_tree.heading(c,text=h); self.alert_tree.column(c, width=120)
        # Scrollbar for alert_tree
        alert_scrollbar = ttk.Scrollbar(a_frame, orient=tk.VERTICAL, command=self.alert_tree.yview)
        self.alert_tree.configure(yscrollcommand=alert_scrollbar.set)
        alert_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.alert_tree.pack(side=tk.LEFT,fill="both", expand=True)
        alerts = fetch_data("SELECT alert_id,line_id,station_id,start_time,end_time,message FROM ServiceAlert")
        for idx, al in enumerate(alerts):
            row_visual_tag = 'oddrow.Treeview' if idx % 2 != 0 else (); tags_to_apply = (row_visual_tag,) if row_visual_tag else ()
            # Format datetime objects if they are not None, else show empty string or placeholder
            al_values = list(al.values())
            for i, val in enumerate(al_values):
                if isinstance(val, datetime):
                    al_values[i] = val.strftime('%Y-%m-%d %H:%M:%S')
                elif val is None and (cols_al[i] == 'start_time' or cols_al[i] == 'end_time'): # Optional: placeholder for None times
                    al_values[i] = 'N/A' 
            self.alert_tree.insert('',tk.END,values=tuple(al_values), tags=tags_to_apply)

    def create_turnstile_tab(self):
        tab = ttk.Frame(self.notebook); self.notebook.add(tab, text="闸机日志")
        t_frame = ttk.LabelFrame(tab, text="进出记录"); t_frame.pack(fill="both", expand=True, padx=10, pady=10) # Standard section padding
        cols_t = ('log_id','passenger_id','station_id','action','timestamp','ticket_id'); self.turnstile_tree = ttk.Treeview(t_frame, columns=cols_t, show='headings', height=12)
        headers = ['日志ID','乘客ID','站点ID','类型','时间','票务ID']
        for c,h in zip(cols_t, headers): self.turnstile_tree.heading(c,text=h); self.turnstile_tree.column(c, width=100)
        # Scrollbar for turnstile_tree
        turnstile_scrollbar = ttk.Scrollbar(t_frame, orient=tk.VERTICAL, command=self.turnstile_tree.yview)
        self.turnstile_tree.configure(yscrollcommand=turnstile_scrollbar.set)
        turnstile_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.turnstile_tree.pack(side=tk.LEFT, fill="both", expand=True)
        logs = fetch_data("SELECT log_id,passenger_id,station_id,action,timestamp,ticket_id FROM TurnstileLog")
        for idx, tl in enumerate(logs):
            row_visual_tag = 'oddrow.Treeview' if idx % 2 != 0 else (); tags_to_apply = (row_visual_tag,) if row_visual_tag else ()
            # Format timestamp if it's a datetime object
            tl_values = list(tl.values())
            if isinstance(tl_values[4], datetime): # Index 4 is 'timestamp'
                tl_values[4] = tl_values[4].strftime('%Y-%m-%d %H:%M:%S')
            self.turnstile_tree.insert('',tk.END,values=tuple(tl_values), tags=tags_to_apply)


# --- Run the Application ---
if __name__ == "__main__":
    # Check if database connection is available at startup
    show_login_dialog()
    conn_test = get_db_connection() # login dialog sets user/pwd in DB_CONFIG
    if conn_test:
        try:
            conn_test.close() # Close the test connection
            app = SubwayApp()
            app.mainloop()
        except Exception as e:
             # Catch potential unexpected errors during app initialization or main loop
             messagebox.showerror("Application Error", f"发生意外错误: {e}")
    else:
        # Display error if connection failed at start
        # Create a temporary root window to show the error message
        root = tk.Tk()
        root.withdraw() # Hide the main useless window
        messagebox.showerror("Startup Failed", "无法连接到数据库，应用程序无法启动。\n请检查 DB_CONFIG 配置和数据库服务状态。")
        root.destroy() # Destroy the temporary window

