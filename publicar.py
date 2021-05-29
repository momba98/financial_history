import subprocess
import datetime

today = datetime.date.today()

print('Dando commit no git. O webapp deve estar atualizados em instantes.')

subprocess.run(["git", "add", "*"])
subprocess.run(["git", "commit", "-m", f"{today}"])
subprocess.run(["git", "push"])

print('Pronto!')

time.sleep(3)
pass
