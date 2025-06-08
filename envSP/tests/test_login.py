from pywinauto.application import Application
import os
import time

python_exe = os.path.abspath(r"..\Scripts\python.exe")
script = os.path.abspath(r"..\ya va\app_princ.py")

print("Python exe:", python_exe)
print("Script:", script)

# Usa un solo string, no una lista
app = Application(backend="uia").start(f'"{python_exe}" "{script}"')
time.sleep(2)

dlg = app.window(title="Liberate App - Login")
dlg.child_window(title="Usuario:", control_type="Edit").type_keys("admin")
dlg.child_window(title="Contraseña:", control_type="Edit").type_keys("admin123")
dlg.child_window(title="Iniciar Sesión", control_type="Button").click()
time.sleep(2)

main = app.window(title_re=".*Liberate App.*")
assert main.exists(), "No se abrió la ventana principal"

print("✅ Prueba de login exitosa.")

app.kill()