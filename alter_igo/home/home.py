from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask import current_app as app
from flask_login import current_user, login_required, logout_user
from ..api import s00, codex_context, numtables, numplots, old_stdout, ldict, runcode, codex_call, log_commands, log_edit, get_log, codex_filename
import re

home_bp = Blueprint('home', __name__,
                    url_prefix='/home',
                    template_folder='templates',
                    static_folder='static')


# basic index route for landing page
@home_bp.route('/')
def index():
    return render_template('index.html')


# route for app
@home_bp.route('/app', methods=['GET'])
@login_required
def app():
    return render_template('home.html')


# route for processing commands
@home_bp.route('/process')
@login_required
def process():
    global codex_context
    print('Received command!')
    command = request.args.get('command').strip()
    raw_command = command
    # wrap multiline commands in quotes for block comments
    if '\n' in command:
        command = "'''\n" + command + "\n'''"
    # prepend single line commands with # for line comments
    else:
        command = '# ' + command
    print(command)

    # check length of codex_context and trim if necessary
    # get positions of each command within the string, clear all but the most recent
    if len(codex_context) > 2000:
        print('Codex prompt is getting too long! Trimming...')
        command_positions = [(m.start(), m.end()) for m in re.finditer('#.+', codex_context)]
        block_key_positions = [(m.start(), m.end()) for m in re.finditer("'''.+'''", codex_context)]
        if len(block_key_positions) > 0:
            if command_positions[-1][0] > block_key_positions[-1][0]:
                codex_context = codex_context[command_positions[-1][0]:]
            else:
                codex_context = codex_context[block_key_positions[-1][0]:]
        else:
            codex_context = codex_context[command_positions[-1][0]:]
    codex_context += '\n' + command + '\n'

    # call openai api using code-davinci-002 to generate code from the command
    print('Calling codex API...')
    response, elapsed = codex_call(codex_context)
    print('Received response from codex API in {0:.2f} seconds.'.format(elapsed))
    codeblock = response.strip()
    print('Received code:\n')
    print(codeblock)

    # if the last line is a declaration, wrap it in a print statement
    # fails if the codeblock is empty, wrap in try-except to avoid erroring out
    try:
        lastline = codeblock.splitlines()[-1]
        if ('=' not in lastline) and ('return' not in lastline) and ('print' not in lastline) and ('.fit' not in lastline) and ('plt' not in lastline):
            lastline_print = 'print(' + lastline + ')'
            codeblock = codeblock.replace(lastline, lastline_print)
            print('Caught last line as a declaration, wrapping in print statement...')
            print('Revised code:\n')
            print(codeblock)
    except IndexError:
        pass

    # strip leading and trailing whitespaces if included
    codex_context += codeblock + '\n'
    [outputtype, output] = runcode(codeblock)
    outputs = [outputtype, raw_command, codeblock, output]

    # write updated codex_context to file
    print('Updating codex prompt...')
    with open(codex_filename, 'w') as f:
        f.write(codex_context)
    
    # commit results to db and get id of corresponding entry
    print('Logging results to database...')
    newest_id = log_commands(outputs)

    # append id to outputs
    outputs.append(newest_id)

    return jsonify(outputs=outputs)


@home_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home.index'))
