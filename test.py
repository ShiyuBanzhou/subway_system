import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
from datetime import datetime

# --- Database Connection Configuration ---
# !!! 修改为你自己的数据库连接信息 !!!
DB_CONFIG = {
    'host': 'localhost',       # 通常是 'localhost' 或 IP 地址
    'user': 'root',            # 使用 root 用户 (根据用户提供的信息)
    'password': '123456',      # 用户密码 (根据用户提供的信息)
    'database': 'subway_system'
    # 'uth_plugin': 'mysql_native_password'
}

# --- Database Interaction Functions ---
# (get_db_connection, fetch_data, execute_query, call_stored_procedure 函数保持不变)
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


# --- GUI Application Class ---
class SubwayApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("地铁信息管理系统 (增强版)")
        self.geometry("950x700") # Increased window size

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
        self.create_train_admin_tab() # Admin features

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


# --- Run the Application ---
if __name__ == "__main__":
    # Check if database connection is available at startup
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

