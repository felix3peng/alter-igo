'''
SETUP
'''
# library imports
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask import current_app as app
from flask_login import current_user, login_required, logout_user
import re
import sys

# local imports
from ..api import s00, s01, codex_context, runcode, codex_call, log_commands, log_edit, get_log, codex_filename, trim_prompt
from ..models import User, db, Log, CodeEdit

# set up variables
old_stdout = sys.stdout
ldict = {}
exec(s00, ldict)
exec(s01, ldict)
numtables = 0
numplots = 0


# initialize blueprint
# home_bp houses landing and app pages, function routes for app
home_bp = Blueprint('home', __name__,
                    url_prefix='/home',
                    template_folder='templates',
                    static_folder='static')


'''
ROUTES
'''
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
    global codex_context, ldict, numtables, numplots
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
    # function will check whether trimming is necessary
    codex_context = trim_prompt(codex_context)
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
        if ('=' not in lastline) and ('return' not in lastline) \
            and ('from' not in lastline) and ('import' not in lastline) \
                and ('print' not in lastline) and ('.fit' not in lastline) and ('plt' not in lastline):
            lastline_print = 'print(' + lastline + ')'
            codeblock = codeblock.replace(lastline, lastline_print)
            print('Caught last line as a declaration, wrapping in print statement...')
            print('Revised code:\n')
            print(codeblock)
    except IndexError:
        pass

    # strip leading and trailing whitespaces if included
    codex_context += codeblock.strip() + '\n'

    # call runcode function to run the codeblock
    [outputtype, output, ldict, numtables, numplots] = runcode(codeblock, ldict, old_stdout, numtables, numplots)
    outputs = [outputtype, raw_command, codeblock, output]

    # write updated codex_context to file
    print('Updating codex prompt...')
    with open(codex_filename, 'w+') as f:
        f.write(codex_context)
    
    # commit results to db and get id of corresponding entry
    print('Logging results to database...')
    newest_id = log_commands(outputs)

    # append id to outputs
    outputs.append(newest_id)

    return jsonify(outputs=outputs)


@home_bp.route('/clear')
@login_required
def clear():
    global codex_context, ldict, numtables, numplots
    codex_context = '# import standard libraries\n' + s00 + '\n'
    ldict = {}
    numtables = 0
    numplots = 0
    exec(codex_context, ldict)
    exec(s01, ldict)
    return jsonify(outputs=[])


# create a function to process positive feedback
@home_bp.route('/positive_feedback')
@login_required
def positive_feedback():
    id = request.args.get('db_id')
    record = Log.query.filter_by(id=id).first()

    # update feedback; none if already positive, positive otherwise
    if record.feedback == 'positive':
        record.feedback = 'none'
        print('Canceled positive feedback on entry', id)
    else:
        record.feedback = 'positive'
        print('Positive feedback on entry', id)
    db.session.commit()
    return jsonify(id=id)


# create a function to process negative feedback
@home_bp.route('/negative_feedback')
@login_required
def negative_feedback():
    id = request.args.get('db_id')
    record = Log.query.filter_by(id=id).first()

    # update feedback; none if already negative, negative otherwise
    if record.feedback == 'negative':
        record.feedback = 'none'
        print('Canceled negative feedback on entry', id)
    else:
        record.feedback = 'negative'
        print('Negative feedback on entry', id)
    db.session.commit()
    return jsonify(id=id)


# create a function to process code edits
@home_bp.route('/edit')
@login_required
def edit():
    global codex_context, ldict, numtables, numplots
    print('Received edit')
    # edit database entry
    record_id = request.args.get('ref')
    newcmd = request.args.get('new_cmd')
    newcode = request.args.get('new_code')

    # retrieve original command and codeblock from Log to overwrite codex_context
    oldcmd, oldcode = get_log(record_id)
    codex_context = codex_context.replace(oldcode, newcode)
    codex_context = codex_context.replace(oldcmd, newcmd)

    # log edit to CodeEdit and Log tables
    # this will add to the CodeEdit table, overwrite command in Log, and increment edit count in Log
    edit = [newcmd, newcode, record_id]
    edit_record_id = log_edit(edit)

    # run edited codeblock and return results
    [outputtype, output, ldict, numtables, numplots] = runcode(newcode, ldict, old_stdout, numtables, numplots)
    outputs = [outputtype, output]

    # commit db changes and return outputs to client
    db.session.commit()
    print('Successfully processed and recorded edit', edit_record_id)
    return jsonify(outputs=outputs) 


# create a function to delete record from db
@home_bp.route('/delete_record')
@login_required
def delete_record():
    global codex_context, ldict, numtables, numplots
    id = request.args.get('db_id')
    print('Received delete request for record', id)
    
    # remove corresponding record from database
    record = Log.query.filter_by(id=id).first()

    # remove corresponding entry from codex prompter
    if '\n' in record.command.strip():
        command = "'''\n" + record.command.strip() + "\n'''"
    else:
        command = '# ' + record.command.strip().replace('\n', '\n# ') + '\n'

    # retrive most recent edit made to this record and use the most recent codeblock
    if record.times_edited > 0:
        last_edit = CodeEdit.query.filter_by(ref_id=id).order_by(id.desc()).first()
        codeblock = last_edit.edited_code.strip() + '\n'
    else:
        codeblock = record.codeblock.strip() + '\n'

    codex_context = codex_context.replace(command, '')
    codex_context = codex_context.replace(codeblock, '')

    # commit changes to db
    db.session.delete(record)
    db.session.commit()

    # write new codex prompt to file
    with open(codex_filename, 'w') as f:
        f.write(codex_context.strip())
    print('Successfully deleted record', id)
    return jsonify(id=id)


@home_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home.index'))
