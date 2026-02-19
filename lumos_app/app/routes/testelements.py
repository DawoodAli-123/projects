#API endpoint to get all Elements from the Repository table

@app.route('/api/testelementlist', methods=['GET'])

def get testelementlist():

conn connection_pool.getconn()

try:

cursor = conn.cursor()

cursor.execute('''SELECT DISTINCT element, xpath, productname, TO_CHAR(lastupd, 'YYYY-MM-DD HH24:MI:SS GMT') AS lastupd, lastupdby FROM Lumos.repository WHERE Inactiveflag 'N' ORDER BY lastupd DESC''')

testelements cursor.fetchall()

except Exception as e:

return jsonify({'error': f"Failed at testelementlist: {str(e)}"}), 400

finally:

cursor.close()

connection_pool.putconn(conn)

return jsonify(testelements), 200

# API endpoint to retrieve Element associated with a given Element name from the Repository table

@app.route('/api/edit_testelement', methods=['GET'])

def edit_testelement():

conn = connection_pool.getconn()

elementname = request.args.get('elementName')

if not elementname:

return jsonify({'error': 'Missing input: Element Name must be specified.')), 400

try:

cursor conn.cursor()

select_query =

SELECT DISTINCT element, xpath, pagetitle, popuptitle, dropdownvalues, defaultvalue, productname FROM Lumos.repository WHERE element %s ORDER BY element;

cursor.execute(select_query, (elementname,))

response = cursor.fetchall()

if not response:

return jsonify({'error': 'No data found for the specified element.')), 404

# Unpack the first row

row response [0]

result = {

"element": row[6],

"xpath": row[1],

"pagetitle": row [2],

"popuptitle": row [3],

"dropdownvalues": row[4],

"defaultvalue": row[5],
"productname": row[6]

return jsonify(result), 200

except Exception as e:

return jsonify({'error': f"Failed at edit_testelement: (str(e))"}), 400

finally:

cursor.close()

connection_pool.putconn(conn)

#API endpoint to create and save a new UI Element in the Repository table

@app.route('/api/save_testelement', methods=['POST'])

def save_testelement():

data request.json

elementname data.get('elementName', '').strip()

xpath data.get('xpath',)

pagetitle data.get('pageTitle',)

popuptitle data.get('popupTitle',)

dropdownvalues data.get('dropdownValues',)

defaultvalue data.get('defaultValue',)

productname data.get('productName',)

username data.get('userName','').strip()

if not elementname:

return jsonify({'error': 'Element name is required.'}), 400

if not username:

return jsonify({'error': 'User name is missing. Please refresh the application.'}), 400

if not xpath: return jsonify({'XPath is required.'}), 400

conn = connection_pool.getconn()

try:

cursor = conn.cursor()

#Check if the Element exists cursor.execute("SELECT COUNT(*) FROM Lumos.repository WHERE element%s AND Inactiveflag %s", (elementname, 'N')) if cursor.fetchone() [8] != 0: return jsonify({'error': f"Element (elementname) already exists."}), 400

cursor.execute("SELECT COUNT(*) FROM Lumos.repository WHERE xpath = %s AND Inactiveflag = %s", (xpath, 'N'))

if cursor.fetchone() [8] != 0: cursor.execute("SELECT element FROM Lumos.repository WHERE xpath=%s AND Inactiveflag = %s", (xpath, 'N')) element = cursor.fetchall()

return jsonify({'error': f"XPath (xpath} already exists and is associated with element(s): (element)."}), 400

if elementname:

cursor.execute(

)

''INSERT INTO lumos.repository

(lastupdby, element, xpath, pagetitle, popuptitle, dropdownvalues, defaultvalue, productname, lastupd) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, DATE_TRUNC('second', CURRENT TIMESTAMP))"

(username, elementname, xpath, pagetitle, popuptitle, dropdownvalues, defaultvalue, productname)

conn.commit()

return jsonify({'message': f"Element (elementname) Created successfully."}), 200

except Exception as e:

return jsonify({'error': f"Failed at save_testelement: {str(e)}"}), 400

finally:

cursor.close()

connection_pool.putconn(conn)

#API endpoint to update a Test Element in the Repository table

@app.route('/api/update_testelement', methods=['PUT'])

def update_testelement():

data = request.json

elementname = data.get('elementName', '').strip()

xpath = data.get('xpath',)

pagetitle = data.get('pageTitle',)

popuptitle = data.get('popupTitle',)
dropdownvalues = data.get('dropdownValues',)

defaultvalue =data.get('defaultValue',)

productname data.get('productName',)

username data.get('userName', '').strip()

if not elementname:

return jsonify({'error': 'Element name is required.')), 408

if not username:

return jsonify({'error': 'User name is missing. Please refresh the application.'}), 400

if not xpath:

return jsonify({'XPath is required.'}), 400

conn connection_pool.getconn()

try:

cursor conn.cursor()

#Check if the Element exists

cursor.execute("SELECT COUNT(*) FROM Lumos.repository WHERE element = %s AND Inactiveflag=%s", (elementname, 'N')) if cursor.fetchone() [8] == 0:

return jsonify({'error': f"Element (elementname) does not exists."}), 400

cursor.execute("SELECT COUNT(*) FROM lumos.repository WHERE xpath = %s AND Inactiveflag = %s", (xpath, 'N'))

if cursor.fetchone() [0] != 0:

try:

cursor.execute("SELECT element FROM Lumos.repository WHERE xpath = %s AND Inactiveflag=%s", (xpath, 'N'))

element = cursor.fetchall()

return jsonify({'error': f"XPath [xpath} already exists and is associated with element(s): (element)."}), 488

if elementname:

)

cursor.execute(

''UPDATE Lumos.repository SET

lastupdby=%s, element=%s, xpath=%s, pagetitle %s, popuptitle=%s,

dropdownvalues=%s, defaultvalue %s, productname %s, lastupd DATE TRUNC('second', CURRENT_TIMESTAMP)

WHERE element = %s;'',

(username, elementname, xpath, pagetitle, popuptitle, dropdownvalues,

defaultvalue, productname, elementname)

#Log activity

log_activity(username=username, action='Update', testcasename='Pack: + elementname, blockname='"')

conn.commit()

return jsonify({'message': f" Test Element {elementname) updated successfully."}), 200

except Exception as e:

conn.rollback() # Rollback in case of error
log_activity(username username, action='Update failed', testcasename='Element: elementname, blockname='')

return jsonify(" Test Element Updation Failed 1: {}".format(e)), 400

except Exception as e:

return jsonify(" Test Element Updation Failed!: {}".format(e)), 400

finally:

cursor.close()

connection_pool.putconn(conn)

#API to Soft-delete a Test Element by marking it inactive in repository tables

@app.route('/api/delete_testelement', methods=['PUT'])

def delete_testelement():

data request.json

elementname data.get('elementName')

username = data.get('userName",").strip()

if not elementname or not username:

return jsonify({'error': Element Name and User Name are required. '), 400

conn = connection_pool.getconn()

try:

try:

cursor conn.cursor()
delete_query = UPDATE lumos.repository SET inactiveflag = %s, lastupdby = %s,

Lastupd = DATE_TRUNC('second', CURRENT_TIMESTAMP)

WHERE element = %s'''

cursor.execute(delete_query, ('Y', username, elementname))

#Log the deletion activity

log_activity(username=username, action='Delete', testcasename='Element elementname, blockname='')

conn.commit()

return jsonify({'message': f'Test Element (elementname) deleted successfully')), 200

except Exception as error:

conn.rollback() # Rollback in case of error

log_activity(username username, action 'Delete failed', testcasename='Element: elementname, blockname='')

return jsonify("Test Element deletion Failed!:

{}".format(error)), 400

except Exception as e:

return jsonify({'error': f"Failed at delete_testelement: {str(e)}"}), 400

finally:

cursor.close()

connection_pool.putconn(conn)