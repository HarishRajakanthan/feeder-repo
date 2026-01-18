import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
import pandas as pd
import os
from tkinter import filedialog, messagebox
from datetime import date,datetime
import datetime as dt
import numpy as np
import time
import traceback
from pathlib import Path
from collections import OrderedDict

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

curr_date = date.today().strftime("%d/%m/%Y")

today = date.today()
prev_year=0

if today.month == 1:
    prev_month_date = date(today.year - 1, 12, 1)
    prev_year = today.year - 1
else:
    prev_month_date = date(today.year, today.month - 1, 1)
    prev_year = today.year

prev_month = prev_month_date.strftime("%b")


# The 3 columns to update with STATIC values

#print(f"Today's date in dd/mm/yyyy format is: {curr_date}")
class FileUpdaterApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("PG2 Utility Invoice Generator (Multi-Key Support)")
        self.geometry("700x900")

        self.csv_template_path = None
        self.var_month = ctk.StringVar(value=prev_month)
        self.var_year = ctk.StringVar(value=prev_year)

        # Data structures to hold file info for each type
        self.files = {
            "Gas": {"path": None, "sheet_var": ctk.StringVar(value="Sheet1"), "ui_dropdown": None, "ui_label": None},
            "Water": {"path": None, "sheet_var": ctk.StringVar(value="Sheet1"), "ui_dropdown": None, "ui_label": None}
        }
        # ==========================================
        # CONFIGURATION
        # ==========================================
        self.CONFIG = {
            "Gas": {
                # Excel: 2 Columns to combine (e.g. Block + Flat)
                "excel_keys": ["Block_Unit", "D/N"],
                "excel_value_col": "AMOUNT",

                # CSV: 2 Columns to match against (e.g. Block + Flat)
                "csv_keys": ["Block", "Flat"],
                "csv_target_col": "Amount1*",

                "static_updates": {
                    "AccountNo1*": "302003",
                    "InvoiceDate(dd/mm/yyyy)*": f"{curr_date}",
                    "Comment1*": ""
                }
            },
            "Water": {
                # Excel: 1 Column (Already unique, e.g. "A-101")
                "excel_keys": ["Unit name"],
                "excel_value_col": "AMOUNT",

                # CSV: 2 Columns (Need to combine to match "A-101")
                "csv_keys": ["Block", "Flat"],
                "csv_target_col": "Amount2*",

                "static_updates": {
                    "AccountNo2*": "301004",
                    "InvoiceDate(dd/mm/yyyy)*": f"{curr_date}",
                    "Comment2*": ""
                }
            }
        }
        # ==========================================

        # Layout Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Gas Box
        self.grid_rowconfigure(1, weight=1)  # Water Box
        self.grid_rowconfigure(2, weight=1)  # CSV Box
        self.grid_rowconfigure(3, weight=1)  # Status
        self.grid_rowconfigure(4, weight=0)  # Button
        self.grid_rowconfigure(5, weight=0)  # Process Button
        self.grid_rowconfigure(6, weight=0)  # Reset Button

        # 1. Date Selection Frame (NEW)
        self.create_date_controls(0)

        # 1. Gas Drop Zone
        self.frame_gas = self.create_smart_drop_zone(1, "Gas", "1. Drop Gas Consumption Here")

        # 2. Water Drop Zone
        self.frame_water = self.create_smart_drop_zone(2, "Water", "2. Drop Water Consumption Here")

        # 3. CSV Drop Zone (Simple)
        self.frame_csv = self.create_simple_drop_zone(3, "3. Drop Template CSV Here", self.load_csv)

        # 4. Status Label
        self.lbl_status = ctk.CTkLabel(self, text="Ready. Drop Gas, Water, or Both.", text_color="gray")
        self.lbl_status.grid(row=4, column=0, pady=10, sticky="ew")

        # 5. Process Button
        self.btn_process = ctk.CTkButton(self, text="Generate Invoice", command=self.process_files, height=50,
                                         font=("Arial", 16, "bold"))
        self.btn_process.grid(row=5, column=0, padx=20, pady=20, sticky="ew")

        # 6. Reset Button (NEW)
        self.btn_reset = ctk.CTkButton(self, text="Reset All", command=self.reset_app, height=40, fg_color="#D32F2F",
                                       hover_color="#B71C1C",font=("Arial", 16, "bold"))
        self.btn_reset.grid(row=6, column=0, padx=20, pady=(0, 20), sticky="ew")

    def create_date_controls(self, row):
        """Creates the Month/Year selection row"""
        frame = ctk.CTkFrame(self)
        frame.grid(row=row, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Label
        lbl = ctk.CTkLabel(frame, text="Select Billing Period:", font=("Arial", 14, "bold"))
        lbl.pack(side="left", padx=20, pady=15)

        # Month Dropdown
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        self.drop_month = ctk.CTkOptionMenu(frame, variable=self.var_month, values=months, width=120)
        self.drop_month.pack(side="left", padx=10)

        # Year Dropdown (Current year -1 to +2)
        curr_year = int(dt.datetime.now().year)
        years = [str(y) for y in range(curr_year - 1, curr_year + 3)]
        self.drop_year = ctk.CTkOptionMenu(frame, variable=self.var_year, values=years, width=100)
        self.drop_year.pack(side="left", padx=10)

    def create_smart_drop_zone(self, row, key, text):
        """Creates a drop zone that includes a hidden sheet dropdown"""
        frame = ctk.CTkFrame(self)
        frame.grid(row=row, column=0, padx=20, pady=10, sticky="nsew")

        frame.drop_target_register(DND_FILES)
        # Bind the drop event to a specific loader for this key (Gas or Water)
        frame.dnd_bind('<<Drop>>', lambda e: self.load_excel(e, key, frame))

        # Main Label
        lbl_title = ctk.CTkLabel(frame, text=text, font=("Arial", 14, "bold"))
        lbl_title.pack(pady=(15, 5))

        # File Name Label (Placeholder)
        lbl_filename = ctk.CTkLabel(frame, text="No file selected", text_color="gray")
        lbl_filename.pack(pady=2)

        # Browse Button
        btn_browse = ctk.CTkButton(frame, text="Browse...", width=100,
                                   command=lambda: self.browse_file(key, frame))
        btn_browse.pack(pady=5)

        # Sheet Selection UI (Hidden initially)
        lbl_sheet = ctk.CTkLabel(frame, text="Select Sheet:", font=("Arial", 11))
        dropdown = ctk.CTkOptionMenu(frame, variable=self.files[key]["sheet_var"], width=150, fg_color="#3B8ED0")

        # Store references so we can update them later
        self.files[key]["ui_label"] = lbl_filename
        self.files[key]["ui_dropdown"] = dropdown
        self.files[key]["ui_sheet_lbl"] = lbl_sheet

        return frame

    def create_simple_drop_zone(self, row, text, command):
        """Simple drop zone for the CSV (No sheet selection needed)"""
        frame = ctk.CTkFrame(self)
        frame.grid(row=row, column=0, padx=20, pady=10, sticky="nsew")
        frame.drop_target_register(DND_FILES)
        frame.dnd_bind('<<Drop>>', command)

        label = ctk.CTkLabel(frame, text=text, font=("Arial", 14, "bold"))
        label.pack(pady=(15, 5))

        btn_browse = ctk.CTkButton(frame, text="Browse...", width=100, command=lambda: self.browse_simple_csv(command))
        btn_browse.pack(pady=10)

        frame.label_ref = label
        return frame

    def browse_file(self, key, frame):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if path:
            class Event: pass

            e = Event()
            e.data = path
            self.load_excel(e, key, frame)

    def browse_simple_csv(self, command_func):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            class Event: pass

            e = Event()
            e.data = path
            command_func(e)

    def clean_path(self, path):
        return path.strip('{}')

    def load_excel(self, event, key, frame):
        path = self.clean_path(event.data)
        try:
            xls = pd.ExcelFile(path)
            sheets = xls.sheet_names

            self.files[key]["path"] = path
            self.files[key]["ui_label"].configure(text=os.path.basename(path), text_color="#4CC9F0")

            # Sheet Logic
            dropdown = self.files[key]["ui_dropdown"]
            lbl_sheet = self.files[key]["ui_sheet_lbl"]
            var = self.files[key]["sheet_var"]

            if len(sheets) > 1:
                var.set(sheets[0])
                dropdown.configure(values=sheets)
                lbl_sheet.pack(pady=(5, 0))
                dropdown.pack(pady=5)
            else:
                var.set(sheets[0])
                lbl_sheet.pack_forget()
                dropdown.pack_forget()

            self.lbl_status.configure(text=f"{key} file loaded.", text_color="gray")

        except Exception as e:
            messagebox.showerror("Error", f"Could not read {key} file:\n{str(e)}")

    def load_excel(self, event, key, frame):
        path = self.clean_path(event.data)
        try:
            xls = pd.ExcelFile(path)
            sheets = xls.sheet_names

            self.files[key]["path"] = path
            self.files[key]["ui_label"].configure(text=os.path.basename(path), text_color="#4CC9F0")

            # Sheet Logic
            dropdown = self.files[key]["ui_dropdown"]
            lbl_sheet = self.files[key]["ui_sheet_lbl"]
            var = self.files[key]["sheet_var"]

            if len(sheets) > 1:
                var.set(sheets[0])
                dropdown.configure(values=sheets)
                lbl_sheet.pack(pady=(5, 0))
                dropdown.pack(pady=5)
            else:
                var.set(sheets[0])
                lbl_sheet.pack_forget()
                dropdown.pack_forget()

            self.lbl_status.configure(text=f"{key} file loaded.", text_color="gray")

        except Exception as e:
            messagebox.showerror("Error", f"Could not read {key} file:\n{str(e)}")

    def load_csv(self, event):
        self.csv_template_path = self.clean_path(event.data)
        self.frame_csv.label_ref.configure(text=f"CSV: {os.path.basename(self.csv_template_path)}",
                                           text_color="#4CC9F0")

    def build_composite_key_excel(self, df, columns):
        """Helper to combine multiple columns into one unique string ID"""
        # Start with the first column
        composite = df[columns[0]].astype(str).str.replace(' - ', '').str.replace('Block-', '')
        #print(composite)
        # If there are more columns, add them with an underscore separator
        for col in columns[1:]:
            composite = composite + "" + df[col].astype(str)
        return composite

    def build_composite_key_csv(self, df, columns):
        """Helper to combine multiple columns into one unique string ID"""
        # Start with the first column
        replacements = {
            '>': '',
            '<': '',
            'Utility ': ''
        }
        composite = df[columns[0]].astype(str).str.replace('>', '').str.replace('<', '').str.replace('Utility ', '')
        # If there are more columns, add them with an underscore separator
        for col in columns[1:]:
            composite = composite  + df[col].astype(str).str.replace('>', '').str.replace('<', '').str.replace('Utility ', '')
        return composite

        # --- NEW RESET FUNCTION ---
    def reset_app(self):
        # 1. Clear Paths
        self.csv_template_path = None

        # 2. Reset Gas and Water UI
        for key in ["Gas", "Water"]:
            self.files[key]["path"] = None
            self.files[key]["sheet_var"].set("Sheet1")

            # Reset Label text
            self.files[key]["ui_label"].configure(text="No file selected", text_color="gray")

            # Hide dropdowns
            self.files[key]["ui_dropdown"].pack_forget()
            self.files[key]["ui_sheet_lbl"].pack_forget()

        # 3. Reset CSV UI
        self.frame_csv.label_ref.configure(text="3. Drop Template CSV Here",
                                           text_color="gray")  # Reset to original text color/content if needed.
        # Or if you just want to reset the color and keep title:
        self.frame_csv.label_ref.configure(text="3. Drop Template CSV Here",
                                           text_color="white" if ctk.get_appearance_mode() == "Dark" else "black")
        # Simpler approach:
        self.frame_csv.label_ref.configure(text="3. Drop Template CSV Here", text_color=("black", "white"))

        # 4. Reset Status
        self.lbl_status.configure(text="Reset Complete. Ready.", text_color="gray")
        # --------------------------
    def process_files(self):
        base_path=""
        mnth = self.var_month.get()
        yr = self.var_year.get()
        self.CONFIG["Gas"]["static_updates"]["Comment1*"] = f"Gas Charges - {mnth} {yr}"
        self.CONFIG["Water"]["static_updates"]["Comment2*"] = f"Water Charges - {mnth} {yr}"
        # 1. Validation
        if not self.csv_template_path:
            messagebox.showerror("Error", "Please upload the Template CSV file.")
            return

        has_gas = self.files["Gas"]["path"] is not None
        has_water = self.files["Water"]["path"] is not None

        if not has_gas and not has_water:
            messagebox.showerror("Error", "Please upload at least one Excel file (Gas or Water).")
            return

        try:
            self.lbl_status.configure(text="Processing...", text_color="orange")
            self.update_idletasks()

            #selected_type = self.utility_var.get()
            #cfg = self.CONFIG[selected_type]
            gas_path = self.files["Gas"]["path"]
            wtr_path = self.files["Water"]["path"]
            # 1. Load Data

            df_csv = pd.read_csv(self.csv_template_path, dtype=str)
            df_csv = df_csv.loc[:, ~df_csv.columns.str.contains('^Unnamed')]
            df_csv['sys_composite_key'] = self.build_composite_key_csv(df_csv, self.CONFIG["Water"]["csv_keys"])

            #print(self.files["Gas"]["sheet_var"])
            #if self.utility_var.get() == "Gas":
            if gas_path is not None:
                df_excel = pd.read_excel(gas_path, dtype=str, sheet_name=self.files["Gas"]["sheet_var"].get(), header=2)
                # 2. Identify Column S (index 18) and Column D (index 3)
                col_s = df_excel.iloc[:, 0]
                #col_d = df_excel.iloc[:, 1]

                # 3. Create a clean "Block" column
                # Logic: Convert column to string -> Check if it starts with "Block"
                # If TRUE: Keep the value. If FALSE (it's a number): Replace with NaN (empty)
                #print(col_s)
                condition = col_s.astype(str).str.startswith("Block", na=False)
                clean_blocks = col_s.where(condition, np.nan)
                #print(clean_blocks)
                # 4. Now Forward Fill the clean blocks
                # This fills the "Block-..." down, ignoring/overwriting the numbers
                filled_blocks = clean_blocks.ffill()
                #print(filled_blocks)

                df_excel['Block_Unit'] = filled_blocks.astype(str)

                for col in self.CONFIG["Gas"]["excel_keys"]:
                    if col not in df_excel.columns:
                        raise ValueError(f"Column '{col}' not found in Gas report.")

                df_excel['sys_composite_key'] = self.build_composite_key_excel(df_excel,
                                                                               self.CONFIG["Gas"]["excel_keys"])

                gas_pending_list = df_excel.loc[df_excel["REMARK"] == "DL", "sys_composite_key"].tolist()

                groups = OrderedDict()
                for code in gas_pending_list:
                    groups.setdefault(code[0], []).append(code)

                result = []
                for block, codes in groups.items():
                    result.extend(["",f"*Block-{block}*"] + codes)

                units_text = "\n".join(result)

                message = (
                    "Dear *Residents*,\n\n"
                    "Gas readings are *pending* for the following units:\n"
                    f"{units_text}\n\n"
                    "Please upload the readings in the group at the earliest to avoid delays in billing.\n\n"
                    "Regards,\n"
                    "Supervisor"
                )
                base_path = Path(gas_path).parent

                with open(f"{base_path}/pending_gas_readings.txt", "w", encoding="utf-8") as f:
                    f.write(message)

                print(df_excel[['sys_composite_key', 'AMOUNT']])
                val_col = self.CONFIG["Gas"]["excel_value_col"]
                if val_col not in df_excel.columns:
                    raise ValueError(f"Value column '{val_col}' not found in Excel file.")
                lookup_map_gas = dict(zip(df_excel['sys_composite_key'], df_excel[val_col]))


            if wtr_path is not None:
                df_excel_wtr = pd.read_excel(wtr_path, dtype=str)

                try:
                    base_path = Path(wtr_path).parent
                    amt = int(df_excel_wtr.loc[2, "AMOUNT"])
                    consmptn= int(df_excel_wtr.loc[2, "Total consumption"])
                    result = amt/consmptn
                    paise=result*100

                    ut_msg=("Dear *Residents*,\n\n"
                        f"The water and gas charges for *{mnth} {yr}* have been updated in ADDA, with the due date set for the 20th of this month.\n\n"
                        f"The water rate has been fixed at *{paise}* paise per litre.\n\n"
                        "Regards,\n"
                        "Supervisor")
                    with open(f"{base_path}/utility_msg.txt", "w", encoding="utf-8") as f:
                        f.write(ut_msg)
                except:
                    print("Not able to generate utility message")
                # 2. Build Excel Composite Key
                # This handles 1 column (Water) or 2 columns (Gas) dynamically
                for col in self.CONFIG["Water"]["excel_keys"]:
                    if col not in df_excel_wtr.columns:
                        raise ValueError(f"Column '{col}' not found in Water report.")

                df_excel_wtr['sys_composite_key'] = self.build_composite_key_excel(df_excel_wtr, self.CONFIG["Water"]["excel_keys"])

                print(df_excel_wtr[['sys_composite_key','AMOUNT']])
                # 3. Build CSV Composite Key
                # This handles the 2 columns in your CSV
                for col in self.CONFIG["Water"]["csv_keys"]:
                    if col not in df_csv.columns:
                        raise ValueError(f"Column '{col}' not found in CSV file.")

                val_col = self.CONFIG["Water"]["excel_value_col"]
                if val_col not in df_excel_wtr.columns:
                    raise ValueError(f"Value column '{val_col}' not found in Excel file.")

                lookup_map_wtr = dict(zip(df_excel_wtr['sys_composite_key'], df_excel_wtr[val_col]))

            if wtr_path is not None and gas_path is not None:
                target_col_gas = self.CONFIG["Gas"]["csv_target_col"]
                target_col_water = self.CONFIG["Water"]["csv_target_col"]
            else:
                target_col_gas = "Amount*"
                target_col_water = "Amount*"

            if wtr_path is not None and gas_path is not None:
                # Perform mapping on our generated keys
                df_csv[target_col_gas] = df_csv['sys_composite_key'].map(lookup_map_gas).astype(float).round(0).fillna(df_csv.get(target_col_gas, ""))
                df_csv[target_col_water] = df_csv['sys_composite_key'].map(lookup_map_wtr).astype(float).round(0).fillna(df_csv.get(target_col_water, ""))

                # 6. Static Updates
                for col, val in self.CONFIG["Gas"]["static_updates"].items():
                    df_csv[col] = val

                for col, val in self.CONFIG["Water"]["static_updates"].items():
                    df_csv[col] = val

            if wtr_path is not None and gas_path is None:
                df_csv[target_col_water] = df_csv['sys_composite_key'].map(lookup_map_wtr).astype(float).round(0).fillna(df_csv.get(target_col_water, ""))
                df_csv["AccountNo*"] = "301004"
                df_csv["Comment*"] = f"Water Charges - {mnth} {yr}"
                df_csv["InvoiceDate(DD/MM/YYYY)*"] = f"{curr_date}"

            if wtr_path is  None and gas_path is not None:
                df_csv[target_col_gas] = df_csv['sys_composite_key'].map(lookup_map_gas).astype(float).round(0).fillna(df_csv.get(target_col_gas, ""))
                df_csv["AccountNo*"] = "302003"
                df_csv["Comment*"] = f"Gas Charges - {mnth} {yr}"
                df_csv["InvoiceDate(DD/MM/YYYY)*"] = f"{curr_date}"

            # 7. Cleanup
            # Remove the temporary key column we created so it doesn't appear in output
            if 'sys_composite_key' in df_csv.columns:
                df_csv = df_csv.drop(columns=['sys_composite_key'])

            # 8. Save
            tstamp= time.time()
            suggested_name = f"Invoice_{tstamp}.csv"
            #base_path = Path(gas_path).parent
            save_path = base_path
            # save_path = filedialog.asksaveasfilename(
            #     initialfile=suggested_name,
            #     defaultextension=".csv",
            #     filetypes=[("CSV files", "*.csv")]
            # )

            if save_path:
                df_csv.to_csv(f"{save_path}/{suggested_name}", index=False)
                self.lbl_status.configure(text=f"Success! Saved {suggested_name} file.", text_color="green")
                messagebox.showinfo("Success", f"{suggested_name} report generated  for {mnth} {yr}!")
            else:
                self.lbl_status.configure(text="Save cancelled.", text_color="gray")

        except Exception as e:
            self.lbl_status.configure(text="Error", text_color="red")

            # 1. Get the full traceback (includes line numbers)
            full_error = traceback.format_exc()

            # 2. Print it to your PyCharm/Terminal console (easier to read)
            print("---------------- ERROR DETAILS ----------------")
            print(full_error)
            print("-----------------------------------------------")

            # 3. Show it in the popup box
            messagebox.showerror("Error", f"An error occurred:\n\n{full_error}")


if __name__ == "__main__":
    app = FileUpdaterApp()
    app.mainloop()
