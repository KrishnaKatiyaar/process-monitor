import psutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import json
import csv
import threading
from datetime import datetime

class ProcessMonitor:
    def __init__(self):
        self.processes = []
        self.sort_column = 'memory_percent'
        self.sort_descending = True

    def get_system_stats(self):
        return {
            "cpu": psutil.cpu_percent(),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent,
            "processes": len(psutil.pids())
        }

    def get_processes(self):
        self.processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 
                                       'memory_percent', 'status', 'create_time']):
            try:
                p = proc.info
                p['create_time'] = datetime.fromtimestamp(p['create_time']).strftime("%H:%M:%S")
                self.processes.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return sorted(self.processes, key=lambda x: x.get(self.sort_column, 0), 
               reverse=self.sort_descending)

    def kill_process(self, pid):
        try:
            psutil.Process(pid).terminate()
            return True
        except:
            return False

    def export_data(self, format):
        filename = f"processes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        processes = self.get_processes()
        if format == 'json':
            with open(filename, 'w') as f:
                json.dump(processes, f, indent=2)
        elif format == 'csv':
            with open(filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=processes[0].keys())
                writer.writeheader()
                writer.writerows(processes)
        return filename

class ProcessMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.monitor = ProcessMonitor()
        self.setup_gui()
        self.update_processes()
        self.update_stats()

    def setup_gui(self):
        self.root.title("Advanced Process Monitor")
        self.root.geometry("1000x600")
        
        # Process List
        self.tree = ttk.Treeview(self.root, columns=('PID', 'Name', 'User', 'CPU%', 'Memory%', 'Status'))
        for col in self.tree['columns']:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort(c))
            self.tree.column(col, width=120)
        self.tree.pack(expand=True, fill='both', padx=10, pady=10)

        # Stats Panel
        self.stats_frame = ttk.Frame(self.root)
        self.stats_vars = {
            'cpu': tk.StringVar(),
            'memory': tk.StringVar(),
            'disk': tk.StringVar(),
            'processes': tk.StringVar()
        }
        for i, (label, var) in enumerate(self.stats_vars.items()):
            ttk.Label(self.stats_frame, text=label.upper()).grid(row=0, column=i, padx=10)
            ttk.Label(self.stats_frame, textvariable=var).grid(row=1, column=i, padx=10)
        self.stats_frame.pack(pady=10)

        # Controls
        control_frame = ttk.Frame(self.root)
        ttk.Button(control_frame, text="Refresh", command=self.update_processes).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Kill Process", command=self.kill_process).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Export JSON", command=lambda: self.export('json')).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Export CSV", command=lambda: self.export('csv')).pack(side='left', padx=5)
        control_frame.pack(pady=10)

    def sort(self, column):
        self.monitor.sort_column = {'PID': 'pid', 'Name': 'name', 'CPU%': 'cpu_percent',
                                  'Memory%': 'memory_percent', 'Status': 'status'}.get(column)
        self.monitor.sort_descending = not self.monitor.sort_descending
        self.update_processes()

    def update_processes(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for proc in self.monitor.get_processes():
            self.tree.insert('', 'end', values=(
                proc['pid'],
                proc['name'][:20],
                proc['username'],
                f"{proc['cpu_percent']:.1f}%",
                f"{proc['memory_percent']:.1f}%",
                proc['status']
            ))

    def update_stats(self):
        stats = self.monitor.get_system_stats()
        for key, var in self.stats_vars.items():
            var.set(f"{stats[key]}%") if key != 'processes' else var.set(stats[key])
        self.root.after(2000, self.update_stats)

    def kill_process(self):
        selected = self.tree.selection()
        if selected:
            pid = self.tree.item(selected[0])['values'][0]
            if messagebox.askyesno("Confirm", f"Kill process {pid}?"):
                if self.monitor.kill_process(pid):
                    self.update_processes()
                else:
                    messagebox.showerror("Error", f"Failed to kill process {pid}")

    def export(self, format):
        filename = self.monitor.export_data(format)
        messagebox.showinfo("Success", f"Data exported to {filename}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProcessMonitorGUI(root)
    root.mainloop()