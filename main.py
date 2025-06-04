import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from tkinter import simpledialog
from datetime import datetime
import os
import csv
import sys

if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)  # exe folder
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

db_path = os.path.join(base_dir, 'data.db')
csv_path = os.path.join(base_dir, 'output.csv')

# Use db_path when connecting SQLite:
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    quantity INTEGER,
    price REAL
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    items TEXT,
    total_price REAL,
    gst REAL,
    final_price REAL
)
""")

conn.commit()


class InventoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Inventory System")
        self.geometry("600x500")
        self.resizable(False, False)

        self.frames = {}
        for F in (LoginPage, SignupPage, Dashboard, AddStockPage, ViewStockPage, SalesPage):
            frame = F(self)
            self.frames[F] = frame
            frame.place(x=0, y=0, relwidth=1, relheight=1)

        self.show_frame(LoginPage)

    def show_frame(self, cont):
        self.frames[cont].tkraise()


class LoginPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Login", font=("Arial", 20)).pack(pady=30)

        form = tk.Frame(self)
        form.pack(pady=10)

        tk.Label(form, text="Username:", font=("Arial", 12)).grid(row=0, column=0, pady=10, sticky='e')
        self.username_entry = tk.Entry(form, font=("Arial", 12), width=25)
        self.username_entry.grid(row=0, column=1, pady=10)

        tk.Label(form, text="Password:", font=("Arial", 12)).grid(row=1, column=0, pady=10, sticky='e')
        self.password_entry = tk.Entry(form, show="*", font=("Arial", 12), width=25)
        self.password_entry.grid(row=1, column=1, pady=10)

        tk.Button(self, text="Login", font=("Arial", 12), command=self.login).pack(pady=10)
        tk.Button(self, text="Don't have an account? Sign up", font=("Arial", 10), fg="blue",
                  command=lambda: master.show_frame(SignupPage)).pack(pady=5)

    def login(self):
        user = self.username_entry.get()
        pwd = self.password_entry.get()

        # Check if username and password are entered
        if not user or not pwd:
            messagebox.showerror("Error", "Please enter both username and password!")
            return

        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd))
        if cursor.fetchone():
            self.master.show_frame(Dashboard)  # Move to Dashboard if valid credentials
        else:
            messagebox.showerror("Error", "Invalid credentials")  # Show error if credentials are incorrect

        # Clear fields after attempt (optional, but useful for re-tries)
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)


class SignupPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Sign Up", font=("Arial", 20)).pack(pady=30)

        form = tk.Frame(self)
        form.pack(pady=10)

        tk.Label(form, text="Username:", font=("Arial", 12)).grid(row=0, column=0, pady=10, sticky='e')
        self.username_entry = tk.Entry(form, font=("Arial", 12), width=25)
        self.username_entry.grid(row=0, column=1, pady=10)

        tk.Label(form, text="Password:", font=("Arial", 12)).grid(row=1, column=0, pady=10, sticky='e')
        self.password_entry = tk.Entry(form, show="*", font=("Arial", 12), width=25)
        self.password_entry.grid(row=1, column=1, pady=10)

        tk.Button(self, text="Sign Up", font=("Arial", 12), command=self.signup).pack(pady=10)
        tk.Button(self, text="Back to Login", font=("Arial", 10),
                  command=lambda: master.show_frame(LoginPage)).pack(pady=5)

    def signup(self):
        user = self.username_entry.get()
        pwd = self.password_entry.get()

        if not user or not pwd:
            messagebox.showerror("Error", "Username and password cannot be empty!")
            return

        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pwd))
            conn.commit()
            messagebox.showinfo("Success", "Account created! Login now.")
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.master.show_frame(LoginPage)
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)


class SalesPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        # Add a label to show the page title
        tk.Label(self, text="Sales History", font=("Arial", 20)).pack(pady=30)

        # Create a frame to hold the Treeview and scrollbar
        tree_frame = tk.Frame(self)
        tree_frame.pack(pady=10, fill="both", expand=True)

        # Bill History Table with Date, Customer Name, Total, GST, Final columns
        self.tree = ttk.Treeview(tree_frame, columns=("Date", "Customer", "Total", "GST", "Final"), show="headings")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Customer", text="Customer")
        self.tree.heading("Total", text="Total Price")
        self.tree.heading("GST", text="GST")
        self.tree.heading("Final", text="Final Price")

        # Set column widths and align numeric columns to the right
        self.tree.column("Date", width=100, anchor="center")
        self.tree.column("Customer", width=150, anchor="center")
        self.tree.column("Total", width=100, anchor="e")
        self.tree.column("GST", width=100, anchor="e")
        self.tree.column("Final", width=100, anchor="e")

        # Pack Treeview
        self.tree.pack(pady=10, fill="both", expand=True, padx=20)

        # Add horizontal scrollbar
        scroll_x = tk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        scroll_x.pack(side="bottom", fill="x")
        self.tree.configure(xscrollcommand=scroll_x.set)

        # Sales data display
        self.sales_info_frame = tk.Frame(self)
        self.sales_info_frame.pack(pady=10)

        # Labels for Total Sales, Total Cost, and Profit/Loss
        self.total_sales_label = tk.Label(self.sales_info_frame, text="Total Sales: Rs. 0.00", font=("Arial", 12))
        self.total_sales_label.grid(row=0, column=0, padx=20, sticky="w")

        self.total_cost_label = tk.Label(self.sales_info_frame, text="Total Cost: Rs. 0.00", font=("Arial", 12))
        self.total_cost_label.grid(row=1, column=0, padx=20, sticky="w")

        self.profit_label = tk.Label(self.sales_info_frame, text="Profit: Rs. 0.00", font=("Arial", 12))
        self.profit_label.grid(row=2, column=0, padx=20, sticky="w")

        self.loss_label = tk.Label(self.sales_info_frame, text="Loss: Rs. 0.00", font=("Arial", 12))
        self.loss_label.grid(row=3, column=0, padx=20, sticky="w")

        # Frame for buttons, ensuring they are placed correctly
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        # Back Button to return to Dashboard
        back_button = tk.Button(button_frame, text="Back to Dashboard", command=lambda: master.show_frame(Dashboard))
        back_button.pack(side="left", padx=10)

        # Refresh Button to reload the sales history
        refresh_button = tk.Button(button_frame, text="Refresh Sales History", command=self.refresh_bill_history)
        refresh_button.pack(side="left", padx=10)

        # Load the initial bill history
        self.load_bill_history()

    def load_bill_history(self):
        try:
            # Clear existing entries in the treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Sales summary vars
            total_sales = 0
            total_cost = 0

            csv_filename = "bill_history.csv"
            if not os.path.exists(csv_filename):
                with open(csv_filename, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Date", "Customer Name", "Item", "Qty", "Price", "Total", "GST", "Final Total"])

            # Load and group bills
            bill_dict = {}  # Key = (Date, Customer, Final Total), Value = summary dict

            with open(csv_filename, mode="r") as file:
                reader = csv.reader(file)
                next(reader)
                for row in reader:
                    bill_date, customer_name, item_name, quantity, price, total_price, gst, final_price = row
                    key = (bill_date, customer_name)
                    if key not in bill_dict:
                        bill_dict[key] = {
                            "total_price": float(total_price),
                            "gst": float(gst),
                            "final_price": float(final_price),
                            "cost": float(price) * int(quantity)
                        }
                    else:
                        bill_dict[key]["total_price"] += float(total_price)
                        bill_dict[key]["gst"] += float(gst)
                        bill_dict[key]["final_price"] += float(final_price)
                        bill_dict[key]["cost"] += float(price) * int(quantity)

            # Populate the table and calculate totals
            for (bill_date, customer_name), values in bill_dict.items():
                self.tree.insert(
                    "", "end",
                    values=(
                        bill_date,
                        customer_name,
                        f"{values['total_price']:.2f}",
                        f"{values['gst']:.2f}",
                        f"{values['final_price']:.2f}"
                    )
                )
                total_sales += values['final_price']
                total_cost += values['cost']

            # Calculate profit/loss
            net = total_sales - total_cost
            profit = net if net >= 0 else 0
            loss = -net if net < 0 else 0

            # Update UI labels
            self.total_sales_label.config(text=f"Total Sales: Rs. {total_sales:.2f}")
            self.total_cost_label.config(text=f"Total Cost: Rs. {total_cost:.2f}")
            self.profit_label.config(text=f"Profit: Rs. {profit:.2f}")
            self.loss_label.config(text=f"Loss: Rs. {loss:.2f}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load sales history.\n{str(e)}")

    def refresh_bill_history(self):
        # Call load_bill_history to refresh the data
        self.load_bill_history()

class Dashboard(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Dashboard", font=("Arial", 20)).pack(pady=30)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="Add Stock", width=20, height=2,
                  command=lambda: master.show_frame(AddStockPage)).pack(pady=5)

        # View Stock Button
        tk.Button(btn_frame, text="View Stock", width=20, height=2,
                  command=lambda: master.show_frame(ViewStockPage)).pack(pady=5)

        # Sales History Button (Moved to the top)
        self.bill_history_button = tk.Button(btn_frame, text="Sales History", width=20, height=2,
                                             command=lambda: master.show_frame(SalesPage))
        self.bill_history_button.pack(pady=5)

        # Logout Button (Moved to below Sales History)
        tk.Button(btn_frame, text="Logout", width=20, height=2, command=lambda: master.show_frame(LoginPage)).pack(
            pady=5)

class AddStockPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Add Stock", font=("Arial", 20)).pack(pady=30)

        form = tk.Frame(self)
        form.pack(pady=10)

        tk.Label(form, text="Item Name:", font=("Arial", 12)).grid(row=0, column=0, pady=10, sticky='e')
        self.name_entry = tk.Entry(form, font=("Arial", 12), width=25)
        self.name_entry.grid(row=0, column=1)

        tk.Label(form, text="Quantity:", font=("Arial", 12)).grid(row=1, column=0, pady=10, sticky='e')
        self.qty_entry = tk.Entry(form, font=("Arial", 12), width=25)
        self.qty_entry.grid(row=1, column=1)

        tk.Label(form, text="Price ₹:", font=("Arial", 12)).grid(row=2, column=0, pady=10, sticky='e')
        self.price_entry = tk.Entry(form, font=("Arial", 12), width=25)
        self.price_entry.grid(row=2, column=1)

        tk.Button(self, text="Add", font=("Arial", 12), command=self.add_item).pack(pady=10)
        tk.Button(self, text="Back to Dashboard", font=("Arial", 10),
                  command=lambda: master.show_frame(Dashboard)).pack(pady=5)

    def add_item(self):
        name = self.name_entry.get().strip()
        qty = self.qty_entry.get().strip()
        price = self.price_entry.get().strip()

        if not name or not qty or not price:
            messagebox.showerror("Error", "All fields are required!")
            return

        try:
            qty = int(qty)
            price = float(price)

            # Check if item already exists with the same name and price
            cursor.execute("SELECT quantity FROM inventory WHERE name = ? AND price = ?", (name, price))
            result = cursor.fetchone()

            if result:
                # If item exists, update quantity
                existing_qty = result[0]
                new_qty = existing_qty + qty
                cursor.execute("UPDATE inventory SET quantity = ? WHERE name = ? AND price = ?", (new_qty, name, price))
            else:
                # If item doesn't exist, insert new
                cursor.execute("INSERT INTO inventory (name, quantity, price) VALUES (?, ?, ?)", (name, qty, price))

            conn.commit()
            messagebox.showinfo("Success", "Item added/updated!")

            # Clear input fields
            self.name_entry.delete(0, tk.END)
            self.qty_entry.delete(0, tk.END)
            self.price_entry.delete(0, tk.END)

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for quantity and price!")

        except sqlite3.DatabaseError as db_err:
            messagebox.showerror("Database Error", f"Database error: {db_err}")

        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")

class ViewStockPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Stock View", font=("Arial", 20)).pack(pady=30)

        # Create treeview to show the inventory
        self.tree = ttk.Treeview(self, columns=("ID", "Name", "Qty", "Price"), show="headings", height=10)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Qty", text="Quantity")
        self.tree.heading("Price", text="Price ₹")
        self.tree.pack(pady=10, fill="x", padx=20)

        # Button frame to hold Refresh, Delete and Back buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack()

        # Refresh button to reload the data
        tk.Button(btn_frame, text="Refresh", font=("Arial", 12), command=self.load_data).pack(side=tk.LEFT, padx=10)

        # Back button to go back to the Dashboard
        tk.Button(btn_frame, text="Back to Dashboard", font=("Arial", 12),
                  command=lambda: master.show_frame(Dashboard)).pack(side=tk.LEFT, padx=10)

        # Delete button to delete the selected stock item
        tk.Button(btn_frame, text="Delete", font=("Arial", 12), command=self.delete_item).pack(side=tk.LEFT, padx=10)

        # Generate Bill button to create a PDF bill
        tk.Button(btn_frame, text="Generate Bill", font=("Arial", 12), command=self.generate_bill).pack(side=tk.LEFT,
                                                                                                        padx=10)

    def load_data(self):
        # Clear the existing entries in the treeview
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Fetch and display data from the inventory table
        cursor.execute("SELECT id, name, quantity, price FROM inventory")
        for row in cursor.fetchall():
            self.tree.insert("", "end", values=row)

    def delete_item(self):
        # Get the selected item (stock) from the treeview
        selected_item = self.tree.selection()

        if not selected_item:
            messagebox.showerror("Error", "Please select an item to delete.")
            return

        # Get the ID of the selected item
        item_id = self.tree.item(selected_item[0])["values"][0]

        # Ask for confirmation before deleting
        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to delete item with ID {item_id}?")

        if confirm:
            try:
                # Delete the selected item from the database
                cursor.execute("DELETE FROM inventory WHERE id=?", (item_id,))
                conn.commit()
                messagebox.showinfo("Success", "Item deleted!")

                # Refresh the treeview after deletion
                self.load_data()

            except sqlite3.DatabaseError as db_err:
                messagebox.showerror("Database Error", f"An error occurred: {db_err}")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def generate_bill(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select at least one item to generate the bill.")
            return

        customer_name = simpledialog.askstring("Customer Name", "Enter the customer's name:")
        if not customer_name:
            return

        total_price = 0
        items_list = []

        for selected_item in selected_items:
            item_values = self.tree.item(selected_item)["values"]
            item_name = item_values[1]
            available_qty = int(item_values[2])
            item_price = float(item_values[3])

            # Ask user for quantity
            purchase_qty = simpledialog.askinteger("Quantity",
                                                   f"Enter quantity for {item_name} (Available: {available_qty}):",
                                                   minvalue=1, maxvalue=available_qty)
            if purchase_qty is None:
                continue  # Skip if cancelled

            if purchase_qty > available_qty:
                messagebox.showwarning("Warning", f"Not enough stock for {item_name}. Skipping item.")
                continue

            total_price += purchase_qty * item_price
            items_list.append((item_name, purchase_qty, item_price, purchase_qty * item_price))

            # Deduct quantity from treeview
            new_qty = available_qty - purchase_qty
            self.tree.item(selected_item, values=(item_values[0], item_name, new_qty, item_price))

        if not items_list:
            messagebox.showerror("Error", "No items were processed for billing.")
            return

        # === Update inventory in database ===
        try:
            conn = sqlite3.connect("inventory.db")  # or your DB file path
            cursor = conn.cursor()
            for name, qty, _, _ in items_list:
                cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE name = ?", (qty, name))
            conn.commit()
            conn.close()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update stock in database: {str(e)}")
            return

        gst = total_price * 0.15
        final_price = total_price + gst

        filename = f"{customer_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        self.create_pdf(items_list, total_price, gst, final_price, customer_name, filename)

        try:
            bill_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            csv_filename = "bill_history.csv"
            file_exists = os.path.exists(csv_filename)

            with open(csv_filename, mode="a", newline="") as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(
                        ["Bill Date", "Customer Name", "Item Name", "Quantity", "Price", "Total Price", "GST",
                         "Final Price"])
                for item in items_list:
                    writer.writerow([bill_date, customer_name, item[0], item[1], item[2], item[3], gst, final_price])

            messagebox.showinfo("Success", "Bill generated, stock updated, and saved to history!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save bill to CSV: {str(e)}")
            print(f"Error: {e}")

    def create_pdf(self, items, total_price, gst, final_price, customer_name, filename):
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter

        # Title
        c.setFont("Helvetica", 16)
        title = "INVENTORY BILL"
        title_width = c.stringWidth(title, "Helvetica", 16)
        c.drawString((width - title_width) / 2, height - 50, title)

        # Date top right
        bill_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.setFont("Helvetica", 8)
        date_width = c.stringWidth(bill_date, "Helvetica", 8)
        c.drawString(width - 100 - date_width, height - 50, f"Bill Date: {bill_date}")

        # Customer name centered
        c.setFont("Helvetica", 12)
        customer_line = f"Customer: {customer_name}"
        cust_width = c.stringWidth(customer_line, "Helvetica", 12)
        c.drawString((width - cust_width) / 2, height - 70, customer_line)

        c.line(50, height - 80, width - 50, height - 80)

        # Items
        y = height - 100
        for item in items:
            line = f"{item[1]} x {item[0]} @ Rs. {item[2]:.2f} = Rs. {item[3]:.2f}"
            lw = c.stringWidth(line, "Helvetica", 12)
            c.drawString((width - lw) / 2, y, line)
            y -= 20

        # Totals
        for i, line in enumerate([
            f"Total Price: Rs. {total_price:.2f}",
            f"GST (15%): Rs. {gst:.2f}",
            f"Final Price: Rs. {final_price:.2f}"
        ]):
            lw = c.stringWidth(line, "Helvetica", 12)
            c.drawString((width - lw) / 2, y - (i * 20), line)

        c.save()

if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()
