import tkinter as tk
from tkinter import messagebox
import requests

SERVER_URL = "http://localhost:5000"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Vacunación Infantil")
        self.root.geometry("400x600")

        self.patient_id = None
        self.worker_id = None
        self.worker_name = None


        self.login_screen()


    def main_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text=f"Responsable: {self.worker_name}", font=("Arial", 10)).pack(pady=5)

        tk.Label(self.root, text="Escanear Beacon", font=("Arial", 16)).pack(pady=20)

        tk.Button(self.root, text="Simular Scan", command=self.scan_beacon).pack(pady=10)

    def scan_beacon(self):
        data = {
            "uuid": "a1b2c3d4-e5f6-7890-1234-56789abcdef0",
            "major": 1,
            "minor": 1001,
            "rssi": -60,
            "source_device": "sim_app" 
        }

        response = requests.post(f"{SERVER_URL}/scan", json=data)

        if response.status_code != 200:
            messagebox.showerror("Error", "Paciente no encontrado")
            return

        patient = response.json()

        self.patient_id = patient["patient_id"]
        self.patient_data = patient

        self.show_patient_screen()

        # pedir alertas clinicas
        alerts_resp = requests.get(f"{SERVER_URL}/check_schedule/{self.patient_id}")

        if alerts_resp.status_code == 200:
            self.alerts_data = alerts_resp.json()
        else:
            self.alerts_data = {"alerts": []}

    def show_scan_logs(self):
        if not self.patient_id:
            messagebox.showwarning("Aviso", "Primero escanea un paciente")
            return

        resp = requests.get(f"{SERVER_URL}/scan_logs/{self.patient_id}")
        if resp.status_code != 200:
            messagebox.showerror("Error", "No se pudieron obtener logs")
            return

        logs = resp.json()

        window = tk.Toplevel(self.root)
        window.title("Logs crudos (BLE)")
        window.geometry("520x420")

        tk.Label(window, text="Logs crudos (BLE)", font=("Arial", 14)).pack(pady=10)

        text = tk.Text(window, wrap="word")
        text.pack(fill="both", expand=True)

        if not logs:
            text.insert("end", "No hay logs aún.\n")
            return

        for l in logs:
            text.insert("end", f"LOG #{l['log_id']}\n")
            text.insert("end", f"patient_id: {l['patient_id']}\n")
            text.insert("end", f"uuid: {l['uuid']}\n")
            text.insert("end", f"major: {l['major']} | minor: {l['minor']}\n")
            text.insert("end", f"rssi: {l['rssi']} dBm\n")
            text.insert("end", f"timestamp: {l['scanned_at']}\n")
            text.insert("end", f"source_device: {l['source_device']}\n")
            text.insert("end", "-" * 40 + "\n")

    def show_patient_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="Datos del Paciente", font=("Arial", 16)).pack(pady=10)
        tk.Label(self.root, text=f"Nombre: {self.patient_data.get('first_name','')}").pack()
        tk.Label(self.root, text=f"Apellido: {self.patient_data.get('last_name','')}").pack()
        tk.Label(self.root, text=f"Nacimiento: {self.patient_data.get('birth_date','')}").pack()

        # --- Alertas clínicas ---
        tk.Label(self.root, text="Alertas clínicas", font=("Arial", 14)).pack(pady=10)

        # Si por alguna razón no se cargaron alertas, evitamos crashear
        alerts_data = getattr(self, "alerts_data", {"alerts": []})
        alerts = alerts_data.get("alerts", [])

        if not alerts:
            tk.Label(self.root, text="Esquema al día").pack()
        else:
            for a in alerts:
                tk.Label(
                    self.root,
                    text=f"⚠ {a['vaccine']}: faltan {a['missing_doses']} dosis (tiene {a['applied_doses']}/{a['required_doses']})",
                    wraplength=360,  # para que no se salga del ancho
                    justify="left"
                ).pack(anchor="w", padx=15, pady=2)

        # --- Botones ---
        tk.Button(self.root, text="Ver Historial", command=self.view_history).pack(pady=10)
        tk.Button(self.root, text="Aplicar Vacuna", command=self.apply_vaccine).pack(pady=10)
        tk.Button(self.root, text="Ver dosis faltantes", command=self.show_missing_doses).pack(pady=10)
        tk.Button(self.root, text="Ver logs crudos", command=self.show_scan_logs).pack(pady=10)


    def view_history(self):
        if not self.patient_id:
            messagebox.showwarning("Aviso", "Primero escanea un paciente")
            return

        response = requests.get(f"{SERVER_URL}/patient_history/{self.patient_id}")

        if response.status_code != 200:
            messagebox.showerror("Error", "No se pudo obtener historial")
            return

        history = response.json()

        if not history:
            messagebox.showinfo("Historial", "Sin vacunas registradas")
            return

        text = ""
        for h in history:
            text += f"{h['vaccine']} | Dosis {h['dose_number']} | {h['date']}\n"

        messagebox.showinfo("Historial", text)


    def apply_vaccine(self):

        response = requests.get(f"{SERVER_URL}/vaccines")

        if response.status_code != 200:
            messagebox.showerror("Error", "No se pudieron obtener vacunas")
            return

        vaccines = response.json()

        window = tk.Toplevel(self.root)
        window.title("Seleccionar Vacuna")
        window.geometry("300x300")

        tk.Label(window, text="Selecciona una vacuna:").pack(pady=10)

        listbox = tk.Listbox(window)
        listbox.pack(fill="both", expand=True)

        for v in vaccines:
            listbox.insert(tk.END, f"{v['id']} - {v['name']}")

        def confirm():

            selection = listbox.curselection()

            if not selection:
                messagebox.showwarning("Aviso", "Selecciona una vacuna")
                return

            selected = vaccines[selection[0]]

            data = {
                "patient_id": self.patient_id,
                "vaccine_id": selected["id"]
            }

            response = requests.post(f"{SERVER_URL}/apply_vaccine", json=data)

            if response.status_code != 200:
                messagebox.showerror("Error", response.json()["error"])
                return

            messagebox.showinfo("Éxito", "Vacuna aplicada correctamente")

            window.destroy()

        tk.Button(window, text="Aplicar", command=confirm).pack(pady=10)

    def show_missing_doses(self):
        alerts_data = getattr(self, "alerts_data", {"alerts": []})
        alerts = alerts_data.get("alerts", [])

        window = tk.Toplevel(self.root)
        window.title("Dosis faltantes")
        window.geometry("420x400")

        tk.Label(window, text="Dosis faltantes", font=("Arial", 14)).pack(pady=10)

        if not alerts:
            tk.Label(window, text="No hay dosis pendientes.").pack(pady=10)
            return

        # Mostrar cada vacuna con detalle
        for a in alerts:
            missing_nums = a.get("missing_dose_numbers", [])
            missing_text = ", ".join(str(n) for n in missing_nums) if missing_nums else "N/A"

            frame = tk.Frame(window, bd=1, relief="solid", padx=10, pady=8)
            frame.pack(fill="x", padx=10, pady=6)

            tk.Label(frame, text=f"Vacuna: {a['vaccine']}", font=("Arial", 11, "bold")).pack(anchor="w")
            tk.Label(frame, text=f"Aplicadas: {a['applied_doses']} / Requeridas: {a['required_doses']}").pack(anchor="w")
            tk.Label(frame, text=f"Faltan: {a['missing_doses']}  (dosis: {missing_text})").pack(anchor="w")

            tk.Button(
                frame,
                text="Aplicar esta vacuna",
                command=lambda vid=a["vaccine_id"], vname=a["vaccine"]: self.apply_selected_vaccine(vid, vname, window)
            ).pack(anchor="e", pady=6)
    

    def apply_selected_vaccine(self, vaccine_id, vaccine_name, parent_window=None):

        if not self.patient_id:
            messagebox.showwarning("Aviso", "Primero escanea un paciente")
            return

        # Aplicar vacuna (esto ya hace validación real en backend)
        response = requests.post(f"{SERVER_URL}/apply_vaccine", json={
            "patient_id": self.patient_id,
            "vaccine_id": vaccine_id,
            "worker_id": self.worker_id
        })

        if not self.worker_id:
            messagebox.showwarning("Aviso", "Primero inicia sesión como responsable")
            return

        if response.status_code != 200:
            try:
                messagebox.showerror("Error", response.json().get("error", "No se pudo aplicar"))
            except:
                messagebox.showerror("Error", "No se pudo aplicar")
            return

        dose = response.json().get("dose_number", "")
        messagebox.showinfo("Éxito", f"Vacuna aplicada: {vaccine_name}\nDosis: {dose}")

        # refrescar alertas después de aplicar
        alerts_resp = requests.get(f"{SERVER_URL}/check_schedule/{self.patient_id}")
        if alerts_resp.status_code == 200:
            self.alerts_data = alerts_resp.json()

        # cerrar ventana de pendientes si existe y refrescar pantalla principal
        if parent_window:
            parent_window.destroy()

        self.show_patient_screen()

    def login_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="Login Responsable", font=("Arial", 16)).pack(pady=20)

        tk.Label(self.root, text="Usuario").pack()
        user_entry = tk.Entry(self.root)
        user_entry.pack(pady=5)

        tk.Label(self.root, text="Contraseña").pack()
        pass_entry = tk.Entry(self.root, show="*")
        pass_entry.pack(pady=5)

        def do_login():
            username = user_entry.get().strip()
            password = pass_entry.get().strip()

            resp = requests.post(f"{SERVER_URL}/login", json={
                "username": username,
                "password": password
            })

            if resp.status_code != 200:
                messagebox.showerror("Error", resp.json().get("error", "Login inválido"))
                return

            data = resp.json()
            self.worker_id = data["worker_id"]
            self.worker_name = data["full_name"]

            messagebox.showinfo("Ok", f"Bienvenido/a: {self.worker_name}")
            self.main_screen()

        tk.Button(self.root, text="Ingresar", command=do_login).pack(pady=15)



if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
