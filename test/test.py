import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
from datetime import datetime

"""# --- Database Connection Configuration ---
DB_CONFIG = {
    'host': 'localhost',       # 通常是 'localhost' 或 IP 地址
    'user': 'root',            # 使用 root 用户 (根据用户提供的信息)
    'password': '1234',      # 用户密码 (根据用户提供的信息)
    'database': 'dbFinal'
    # 'uth_plugin': 'mysql_native_password'
} """

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dbFinal'
    # 'user' 和 'password' 不要写死
}

def show_login_dialog():
    login = tk.Tk()
    login.title("地铁管理系统账户登录")
    login.geometry("400x180")
    tk.Label(login, text="账号:").grid(row=0, column=0, padx=10, pady=10)
    user_var = tk.StringVar()
    user_entry = tk.Entry(login, textvariable=user_var)
    user_entry.grid(row=0, column=1, padx=10, pady=10)
    tk.Label(login, text="密码:").grid(row=1, column=0, padx=10, pady=10)
    pwd_var = tk.StringVar()
    pwd_entry = tk.Entry(login, textvariable=pwd_var, show="*")
    pwd_entry.grid(row=1, column=1, padx=10, pady=10)

    def try_login():
        username = user_var.get()
        password = pwd_var.get()
        if not username or not password:
            messagebox.showerror("错误", "请填写账号和密码")
            return
        # 这里设置全局DB_CONFIG
        global DB_CONFIG
        DB_CONFIG['user'] = username
        DB_CONFIG['password'] = password
        # 尝试连接
        try:
            conn = mysql.connector.connect(**DB_CONFIG, auth_plugin='mysql_native_password')
            conn.close()
            messagebox.showinfo("登陆成功", f"欢迎 {username} ！")
            login.destroy()
        except mysql.connector.Error as err:
            messagebox.showerror("登录失败", f"数据库错误: {err}")

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

"""class SubwayMapMixin:
    def create_map_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="线路地图")

        # 创建 Canvas，用于绘制地图和滚动
        container = ttk.Frame(tab)
        container.pack(fill=tk.BOTH, expand=True)
        self.map_canvas = tk.Canvas(container, bg="#f0f0f0")
        h_scroll = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=self.map_canvas.xview)
        v_scroll = ttk.Scrollbar(container, orient=tk.VERTICAL,   command=self.map_canvas.yview)
        self.map_canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        self.map_canvas.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # 调色板用于不同线路
        palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

        # 动态加载线路和站点
        lines = fetch_data("SELECT line_id, line_name FROM `line` WHERE status='运营' ORDER BY line_id")
        self.map_objects = []
        self.map_station_names = set()
        y_base = 100
        y_gap  = 100
        for idx, line in enumerate(lines):
            lid = line['line_id']
            name = line['line_name']
            color = palette[idx % len(palette)]
            # 查询该线路所有站点，按 station_id 排序
            stations = fetch_data(
                "SELECT station_name FROM `station` WHERE line_id=%s ORDER BY station_id", (lid,)
            )
            count = len(stations)
            if count == 0:
                continue
            # 计算 X 间距，留边距
            margin = 50
            width = (self.map_canvas.winfo_width() or 600)
            x_gap = max(100, (width - 2*margin) / (count - 1))
            y = y_base + idx * y_gap
            coords = []
            # 绘制线路连接线
            for i, st in enumerate(stations):
                x = margin + i * x_gap
                coords.extend([x, y])
            self.map_canvas.create_line(*coords, fill=color, width=6, capstyle=tk.ROUND, tags=(f'line_{lid}',))
            # 绘制站点圆点与站名
            for i, st in enumerate(stations):
                station_name = st['station_name']
                self.map_station_names.add(station_name)
                x = margin + i * x_gap
                self.map_canvas.create_oval(
                    x-8, y-8, x+8, y+8,
                    fill=color, outline='white', width=2,
                    tags=('station_dot', station_name)
                )
                self.map_canvas.create_text(
                    x, y-20, text=station_name,
                    font=('Helvetica', 10, 'bold'), fill=color,
                    tags=('station_text', station_name)
                )
        # 配置滚动区域
        self.map_canvas.update_idletasks()
        bbox = self.map_canvas.bbox(tk.ALL)
        if bbox:
            self.map_canvas.config(scrollregion=bbox)

        # 绑定点击事件，仅对站点圆点
        self.map_canvas.tag_bind('station_dot', '<Button-1>', self.on_map_station_click)

    def on_map_station_click(self, event):
        items = self.map_canvas.find_withtag(tk.CURRENT)
        if not items:
            return
        tags = self.map_canvas.gettags(items[0])
        # 从 tags 中提取真实站点名称
        station_name = next((t for t in tags if t in self.map_station_names), None)
        if station_name:
            self.show_station_popup(station_name)"""


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
        self.geometry("1080x720") # Increased window size

        # --- Style ---
        style = ttk.Style(self)
        style.theme_use('clam') # Or 'alt', 'default', 'classic'
        # Configure Treeview highlighting for transfer stations using tags
        style.configure('Transfer.Treeview', foreground='blue', font=('TkDefaultFont', 10, 'bold'))
        style.configure('Normal.Treeview', font=('TkDefaultFont', 10))
        # Configure selected item appearance
        style.map('Transfer.Treeview', background=[('selected', '#ADD8E6')], foreground=[('selected', 'black')]) # Light blue background on select
        style.map('Normal.Treeview', background=[('selected', '#ADD8E6')], foreground=[('selected', 'black')])


        # --- Main Notebook (Tabbed Interface) ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # --- Store station data for easy access ---
        self.station_details = {} # Store details like id, is_transfer by item id (Treeview's internal ID)

        # --- Create Tabs ---
        self.create_line_station_tab()
        self.create_schedule_tab()
        self.create_ticket_tab()
        self.create_train_admin_tab()
        self.create_fare_tab()
        self.create_staff_tab()
        self.create_maint_tab()
        self.create_alert_tab()
        self.create_turnstile_tab()
        self.create_map_tab()


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
            # Fetch station data including id and transfer status
            query = """
                SELECT station_id, station_name, location_desc, is_transfer
                FROM Station
                WHERE line_id = %s
                ORDER BY station_id
            """
            stations = fetch_data(query, (line_id,))
            for station in stations:
                # Determine style tag based on transfer status
                tag_style = 'Transfer.Treeview' if station['is_transfer'] else 'Normal.Treeview'
                # Insert into treeview
                item_id = self.station_tree.insert('', tk.END, values=(
                    station['station_name'],
                    station['location_desc'] if station['location_desc'] else '暂无描述' # Handle null description
                ), tags=(tag_style,)) # Apply the tag here
                # Store station details for later use, using the Treeview item ID as the key
                self.station_details[item_id] = {
                    'id': station['station_id'],
                    'name': station['station_name'],
                    'is_transfer': station['is_transfer'],
                    'line_id': line_id # Store current line_id for transfer check
                }

    def on_station_select(self, event=None):
        """Called when a station is selected in the Treeview"""
        # Ensure widgets exist before accessing them
        if not hasattr(self, 'station_tree') or not hasattr(self, 'poi_tree') or \
           not hasattr(self, 'transfer_button') or not hasattr(self, 'transfer_label'):
            return # Widgets not ready yet

        selected_items = self.station_tree.selection()
        if not selected_items:
            self.transfer_button.config(state=tk.DISABLED)
            self.transfer_label.config(text="请先在左侧选择一个换乘站")
            # Clear POI list
            for i in self.poi_tree.get_children():
                self.poi_tree.delete(i)
            return

        item_id = selected_items[0] # Get the internal ID of the selected item
        station_info = self.station_details.get(item_id)

        if station_info:
            station_id = station_info['id']
            station_name = station_info['name']
            is_transfer = station_info['is_transfer']

            # --- Update POI List ---
            # Clear previous POIs
            for i in self.poi_tree.get_children():
                self.poi_tree.delete(i)
            # Fetch and display new POIs
            pois = fetch_pois_for_station(station_id)
            if pois:
                for poi in pois:
                    self.poi_tree.insert('', tk.END, values=(
                        poi['poi_name'],
                        poi['category'] if poi['category'] else '其他',
                        poi['description'] if poi['description'] else ''
                    ))
            else:
                 # Insert a placeholder if no POIs found
                 self.poi_tree.insert('', tk.END, values=('该站点暂无周边信息记录', '', ''), tags=('placeholder',))


            # --- Update Transfer Info ---
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

        search_button = ttk.Button(input_frame, text="查询时刻表", command=self.load_schedule)
        search_button.grid(row=1, column=2, padx=10, pady=5)

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
            query = """
                SELECT
                    t.train_number,
                    l.line_name,
                    sch.arrival_time,
                    sch.departure_time
                FROM
                    Schedule sch
                JOIN
                    Train t ON sch.train_id = t.train_id
                JOIN
                    Station s ON sch.station_id = s.station_id
                JOIN
                    Line l ON t.line_id = l.line_id
                WHERE
                    sch.station_id = %s AND sch.schedule_date = %s
                ORDER BY
                    sch.arrival_time, sch.departure_time
            """
            schedules = fetch_data(query, (station_id, selected_date))
            if schedules:
                for schedule in schedules:
                    # Format time display, handle None or timedelta
                    arrival_val = schedule['arrival_time']
                    departure_val = schedule['departure_time']

                    arrival_str = arrival_val.strftime('%H:%M:%S') if hasattr(arrival_val, 'strftime') else str(arrival_val) if arrival_val else "---"
                    departure_str = departure_val.strftime('%H:%M:%S') if hasattr(departure_val, 'strftime') else str(departure_val) if departure_val else "---"

                    self.schedule_display_tree.insert('', tk.END, values=(
                        schedule['train_number'],
                        schedule['line_name'],
                        arrival_str,
                        departure_str
                    ))
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


        ttk.Label(ticket_frame, text="出发站:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.ticket_dep_station_combobox = ttk.Combobox(ticket_frame, state="readonly", width=30)
        self.ticket_dep_station_combobox.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(ticket_frame, text="到达站:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.ticket_arr_station_combobox = ttk.Combobox(ticket_frame, state="readonly", width=30)
        self.ticket_arr_station_combobox.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(ticket_frame, text="票价:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.ticket_price_entry = ttk.Entry(ticket_frame, width=10)
        self.ticket_price_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(ticket_frame, text="元 (实际票价应由系统计算)").grid(row=3, column=2, padx=5, pady=5, sticky=tk.W)


        buy_button = ttk.Button(ticket_frame, text="确认购买 (调用存储过程)", command=self.buy_ticket)
        buy_button.grid(row=4, column=0, columnspan=3, pady=10)

        # Load stations into ticketing comboboxes
        self.load_stations_for_ticketing()

    def load_stations_for_ticketing(self):
        """Load all station names into the ticketing comboboxes"""
        stations = fetch_data("SELECT station_id, station_name FROM Station ORDER BY station_name")
        station_names = [s['station_name'] for s in stations]
        self.ticket_station_data = {s['station_name']: s['station_id'] for s in stations}

        # Ensure comboboxes exist before setting values
        if hasattr(self, 'ticket_dep_station_combobox') and hasattr(self, 'ticket_arr_station_combobox'):
            self.ticket_dep_station_combobox['values'] = station_names
            self.ticket_arr_station_combobox['values'] = station_names
            if station_names:
                self.ticket_dep_station_combobox.current(0)
                self.ticket_arr_station_combobox.current(1 if len(station_names) > 1 else 0)


    def buy_ticket(self):
        """Call the stored procedure to purchase a ticket"""
        # Ensure widgets exist
        if not hasattr(self, 'ticket_passenger_id_entry') or \
           not hasattr(self, 'ticket_price_entry') or \
           not hasattr(self, 'ticket_dep_station_combobox') or \
           not hasattr(self, 'ticket_arr_station_combobox'):
            return

        passenger_id_str = self.ticket_passenger_id_entry.get()
        price_str = self.ticket_price_entry.get()

        if not passenger_id_str or not price_str:
             messagebox.showerror("Input Error", "乘客ID和票价不能为空。")
             return

        try:
            passenger_id = int(passenger_id_str)
            price = float(price_str)
            if price <= 0:
                 messagebox.showerror("Input Error", "票价必须是大于0的数字。")
                 return
        except ValueError:
            messagebox.showerror("Input Error", "乘客ID和票价必须是有效的数字。")
            return

        dep_station_name = self.ticket_dep_station_combobox.get()
        arr_station_name = self.ticket_arr_station_combobox.get()

        if not dep_station_name or not arr_station_name:
            messagebox.showwarning("Selection Incomplete", "请选择出发站和到达站。")
            return

        if dep_station_name == arr_station_name:
            messagebox.showwarning("Selection Error", "出发站和到达站不能相同。")
            return

        dep_station_id = self.ticket_station_data.get(dep_station_name)
        arr_station_id = self.ticket_station_data.get(arr_station_name)

        if not dep_station_id or not arr_station_id:
            messagebox.showerror("Internal Error", "无法找到选择的站点ID。")
            return

        # Call stored procedure sp_purchase_ticket
        # Args order: p_passenger_id, p_departure_station_id, p_arrival_station_id, p_price, OUT p_ticket_id, OUT p_message
        args = (passenger_id, dep_station_id, arr_station_id, price, 0, '') # Initial OUT parameter values
        results = call_stored_procedure('sp_purchase_ticket', args)

        if results:
            # Results tuple matches procedure definition order
            ticket_id = results[4] # 5th element is p_ticket_id (OUT)
            message = results[5]   # 6th element is p_message (OUT)
            if ticket_id: # Purchase successful (procedure returned a ticket_id)
                messagebox.showinfo("Purchase Result", f"{message}\n票务ID: {ticket_id}")
                # Optionally clear fields after successful purchase
                # self.ticket_passenger_id_entry.delete(0, tk.END)
                # self.ticket_price_entry.delete(0, tk.END)
            else: # Purchase failed
                messagebox.showerror("Purchase Failed", message)
        # else: Connection or procedure call itself failed, error already shown


    # --- Tab 4: Train Management (Mostly unchanged) ---
    def create_train_admin_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="列车管理 (管理员)")

        # Train List Frame
        list_frame = ttk.LabelFrame(tab, text="列车列表")
        list_frame.pack(pady=10, padx=10, fill="both", expand=True)

        cols_train = ('train_id', 'train_number', 'line_name', 'model', 'capacity', 'status')
        # --- RENAME train_tree to avoid conflict if needed, but should be ok ---
        self.train_admin_tree = ttk.Treeview(list_frame, columns=cols_train, show='headings', height=10, selectmode="browse")
        self.train_admin_tree.heading('train_id', text='ID')
        self.train_admin_tree.heading('train_number', text='列车编号')
        self.train_admin_tree.heading('line_name', text='所属线路')
        self.train_admin_tree.heading('model', text='型号')
        self.train_admin_tree.heading('capacity', text='容量')
        self.train_admin_tree.heading('status', text='状态')
        self.train_admin_tree.column('train_id', width=50, anchor=tk.CENTER, stretch=tk.NO)
        self.train_admin_tree.column('train_number', width=100)
        self.train_admin_tree.column('line_name', width=150)
        self.train_admin_tree.column('model', width=100)
        self.train_admin_tree.column('capacity', width=80, anchor=tk.E)
        self.train_admin_tree.column('status', width=80, anchor=tk.CENTER)

        scrollbar_train = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.train_admin_tree.yview)
        self.train_admin_tree.configure(yscroll=scrollbar_train.set)
        scrollbar_train.pack(side=tk.RIGHT, fill=tk.Y)
        self.train_admin_tree.pack(side=tk.LEFT, fill="both", expand=True)

        self.train_admin_tree.bind('<<TreeviewSelect>>', self.on_train_select) # Bind selection event

        # Action Frame
        action_frame = ttk.Frame(tab)
        action_frame.pack(pady=10, padx=10, fill="x")

        refresh_button = ttk.Button(action_frame, text="刷新列表", command=self.load_trains)
        refresh_button.pack(side=tk.LEFT, padx=5)

        ttk.Label(action_frame, text="选中列车ID:").pack(side=tk.LEFT, padx=5)
        self.selected_train_id_label = ttk.Label(action_frame, text="未选择", width=10)
        self.selected_train_id_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(action_frame, text="新状态:").pack(side=tk.LEFT, padx=5)
        self.new_status_combobox = ttk.Combobox(action_frame, values=['运行中', '维修中'], state="readonly", width=10)
        self.new_status_combobox.pack(side=tk.LEFT, padx=5)

        update_button = ttk.Button(action_frame, text="更新状态 (触发器记录日志)", command=self.update_train_status)
        update_button.pack(side=tk.LEFT, padx=5)

        # Load initial data
        self.load_trains()

    def load_trains(self):
        """Load all train info into the admin Treeview"""
        # Ensure widgets exist
        if not hasattr(self, 'train_admin_tree') or \
           not hasattr(self, 'selected_train_id_label') or \
           not hasattr(self, 'new_status_combobox'):
            return

        # Clear old data
        for i in self.train_admin_tree.get_children():
            self.train_admin_tree.delete(i)
        self.selected_train_id_label.config(text="未选择") # Reset selected ID display
        self.new_status_combobox.set('') # Clear status selection

        query = """
            SELECT
                t.train_id, t.train_number, l.line_name, t.model, t.capacity, t.status
            FROM
                Train t
            JOIN
                Line l ON t.line_id = l.line_id
            ORDER BY
                t.train_id
        """
        trains = fetch_data(query)
        for train in trains:
            self.train_admin_tree.insert('', tk.END, values=(
                train['train_id'],
                train['train_number'],
                train['line_name'],
                train['model'] if train['model'] else 'N/A',
                train['capacity'] if train['capacity'] else 'N/A',
                train['status']
            ))

    def on_train_select(self, event=None):
        """Called when a train is selected in the admin Treeview"""
        # Ensure widgets exist
        if not hasattr(self, 'train_admin_tree') or \
           not hasattr(self, 'selected_train_id_label') or \
           not hasattr(self, 'new_status_combobox'):
            return

        selected_items = self.train_admin_tree.selection()
        if selected_items:
            item = self.train_admin_tree.item(selected_items[0])
            train_id = item['values'][0]
            current_status = item['values'][5]
            self.selected_train_id_label.config(text=str(train_id))
            # Set combobox to the current status
            if current_status in self.new_status_combobox['values']:
                self.new_status_combobox.set(current_status)
            else:
                 self.new_status_combobox.set('') # Clear if status is invalid
        else:
            self.selected_train_id_label.config(text="未选择")
            self.new_status_combobox.set('')


    def update_train_status(self):
        """Update the status of the selected train"""
        # Ensure widgets exist
        if not hasattr(self, 'train_admin_tree') or \
           not hasattr(self, 'new_status_combobox'):
            return

        selected_items = self.train_admin_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "请先在列表中选择一辆列车。")
            return

        item = self.train_admin_tree.item(selected_items[0])
        train_id = item['values'][0]
        current_status = item['values'][5]
        new_status = self.new_status_combobox.get()

        if not new_status:
            messagebox.showwarning("No Status Selected", "请选择新的状态。")
            return

        if new_status == current_status:
            messagebox.showinfo("No Update Needed", "新状态与当前状态相同。")
            return

        # Confirmation dialog
        confirm = messagebox.askyesno("Confirm Update", f"确定要将列车 ID {train_id} 的状态从 '{current_status}' 更新为 '{new_status}' 吗？\n(此操作将触发日志记录)")

        if confirm:
            query = "UPDATE Train SET status = %s WHERE train_id = %s"
            result = execute_query(query, (new_status, train_id))
            if result is not None: # execute_query success doesn't always return ID for UPDATE
                 messagebox.showinfo("Update Successful", f"列车 {train_id} 的状态已更新为 '{new_status}'。")
                 self.load_trains() # Refresh list to show the new status
                 # Trigger automatically logs the change
            # else: Error message already shown in execute_query

        # --- Tab 5: 票价与票种管理 ---
    def create_fare_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="票价管理")

        # FareZone Tree
        fz_frame = ttk.LabelFrame(tab, text="分区票价")
        fz_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)
        cols_fz = ('zone_id', 'zone_name', 'description')
        self.fz_tree = ttk.Treeview(fz_frame, columns=cols_fz, show='headings', height=10)
        for c, h in zip(cols_fz, ['ID', '分区', '描述']):
            self.fz_tree.heading(c, text=h)
            self.fz_tree.column(c, width=100)
        self.fz_tree.pack(fill="both", expand=True)
        
        # TicketType Tree
        tt_frame = ttk.LabelFrame(tab, text="票种规则")
        tt_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)
        cols_tt = ('type_id', 'type_name', 'base_price', 'validity_minutes')
        self.tt_tree = ttk.Treeview(tt_frame, columns=cols_tt, show='headings', height=10)
        for c, h, w in zip(cols_tt, ['ID','票种','基础价','有效期(分)'], [50,100,80,80]):
            self.tt_tree.heading(c, text=h)
            self.tt_tree.column(c, width=w)
        self.tt_tree.pack(fill="both", expand=True)

        # Load data
        for zone in fetch_data("SELECT zone_id, zone_name, description FROM FareZone"):
            self.fz_tree.insert('', tk.END, values=(zone['zone_id'], zone['zone_name'], zone['description']))
        for tp in fetch_data("SELECT type_id, type_name, base_price, validity_minutes FROM TicketType"):
            self.tt_tree.insert('', tk.END, values=(tp['type_id'], tp['type_name'], tp['base_price'], tp['validity_minutes']))

    # --- Tab 6: 员工与排班 ---
    def create_staff_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="员工排班")

        # Staff List
        staff_frame = ttk.LabelFrame(tab, text="员工列表")
        staff_frame.pack(side=tk.TOP, fill="x", padx=5, pady=5)
        cols_s = ('staff_id','name','role','contact')
        self.staff_tree = ttk.Treeview(staff_frame, columns=cols_s, show='headings', height=5)
        for c,h in zip(cols_s, ['ID','姓名','岗位','联系方式']):
            self.staff_tree.heading(c, text=h); self.staff_tree.column(c, width=100)
        self.staff_tree.pack(fill="x")
        for s in fetch_data("SELECT staff_id,name,role,contact FROM Staff"):
            self.staff_tree.insert('',tk.END,values=(s['staff_id'],s['name'],s['role'],s['contact']))

        # Assignment List
        assign_frame = ttk.LabelFrame(tab, text="排班记录")
        assign_frame.pack(side=tk.TOP, fill="both", expand=True, padx=5, pady=5)
        cols_a = ('assign_id','staff_id','station_id','start_time','end_time')
        self.assign_tree = ttk.Treeview(assign_frame, columns=cols_a, show='headings', height=8)
        for c,h in zip(cols_a, ['排班ID','员工ID','站点ID','开始','结束']):
            self.assign_tree.heading(c, text=h); self.assign_tree.column(c, width=100)
        self.assign_tree.pack(fill="both", expand=True)
        for a in fetch_data("SELECT assign_id,staff_id,station_id,start_time,end_time FROM StaffAssignment"):
            self.assign_tree.insert('',tk.END,values=(a['assign_id'],a['staff_id'],a['station_id'],a['start_time'],a['end_time']))

    # --- Tab 7: 维保记录 ---
    def create_maint_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="设备维保")

        m_frame = ttk.LabelFrame(tab, text="维护记录")
        m_frame.pack(fill="both", expand=True, padx=5, pady=5)
        cols_m = ('record_id','equipment','station_id','staff_id','start_time','end_time','description')
        self.maint_tree = ttk.Treeview(m_frame, columns=cols_m, show='headings', height=12)
        headers = ['ID','设备','站点','员工','开始','结束','备注']
        for c,h in zip(cols_m, headers):
            self.maint_tree.heading(c,text=h); self.maint_tree.column(c, width=100)
        self.maint_tree.pack(fill="both", expand=True)
        for r in fetch_data("SELECT record_id,equipment,station_id,staff_id,start_time,end_time,description FROM MaintenanceRecord"):
            self.maint_tree.insert('',tk.END,values=tuple(r.values()))

    # --- Tab 8: 服务公告 ---
    def create_alert_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="服务公告")

        a_frame = ttk.LabelFrame(tab, text="公告列表")
        a_frame.pack(fill="both", expand=True, padx=5, pady=5)
        cols_al = ('alert_id','line_id','station_id','start_time','end_time','message')
        self.alert_tree = ttk.Treeview(a_frame, columns=cols_al, show='headings', height=12)
        headers = ['ID','线路ID','站点ID','开始','结束','内容']
        for c,h in zip(cols_al, headers):
            self.alert_tree.heading(c,text=h); self.alert_tree.column(c, width=120)
        self.alert_tree.pack(fill="both", expand=True)
        for al in fetch_data("SELECT alert_id,line_id,station_id,start_time,end_time,message FROM ServiceAlert"):
            self.alert_tree.insert('',tk.END,values=tuple(al.values()))

    # --- Tab 9: 闸机进出 ---
    def create_turnstile_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="闸机日志")

        t_frame = ttk.LabelFrame(tab, text="进出记录")
        t_frame.pack(fill="both", expand=True, padx=5, pady=5)
        cols_t = ('log_id','passenger_id','station_id','action','timestamp','ticket_id')
        self.turnstile_tree = ttk.Treeview(t_frame, columns=cols_t, show='headings', height=12)
        headers = ['日志ID','乘客ID','站点ID','类型','时间','票务ID']
        for c,h in zip(cols_t, headers):
            self.turnstile_tree.heading(c,text=h); self.turnstile_tree.column(c, width=100)
        self.turnstile_tree.pack(fill="both", expand=True)
        for tl in fetch_data("SELECT log_id,passenger_id,station_id,action,timestamp,ticket_id FROM TurnstileLog"):
            self.turnstile_tree.insert('',tk.END,values=tuple(tl.values()))

# --- Run the Application ---
if __name__ == "__main__":
    # Check if database connection is available at startup
    show_login_dialog()
    conn_test = get_db_connection()
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

