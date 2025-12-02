import re
with open('e:\\Shakour\\GravityProjects\\GravityWaves_TseTmc\\api\\Gravity_tse.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
def_line = None
return_line = None
for i, line in enumerate(lines):
    if 'def Get_MarketWatch' in line:
        def_line = i
    if 'return final_df, final_OB_df' in line:
        return_line = i
if def_line is not None and return_line is not None:
    lines.insert(def_line + 1, '    try:\n')
    for i in range(def_line + 2, return_line + 2):
        lines[i] = '    ' + lines[i]
    lines[return_line + 1] = '        return final_df, final_OB_df\n'
    lines.insert(return_line + 2, '    except Exception as e:\n')
    lines.insert(return_line + 3, '        print(f"Error in Get_MarketWatch: {e}")\n')
    lines.insert(return_line + 4, '        return None, None\n')
    with open('e:\\Shakour\\GravityProjects\\GravityWaves_TseTmc\\api\\Gravity_tse.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)