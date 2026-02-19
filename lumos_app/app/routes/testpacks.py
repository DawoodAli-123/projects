#API endpoint to get all Test Packs from the Testpack list table

@app.route('/api/testpacklist', methods=['GET'])

def get_testpacklist():

conn connection_pool.getconn()

try:

cursor conn.cursor()

cursor.execute('SELECT DISTINCT testpack_name, TO_CHAR(lastupd, 'YYYY-MM-DD HH24:MI:SS GMT') AS lastupd, lastupdby FROM lumos.testpack list WHERE Inactiveflag 'N' ORDER BY testpack_name')

testpacks cursor.fetchall()

except Exception as e:

return jsonify({'error': f"Failed at testpacklist: {str(e)}")), 400

finally:

cursor.close()

connection_pool.putconn(conn)

return jsonify (testpacks), 200

#API endpoint to retrieve a list of all active test cases @app.route("/api/populate_testcases', methods=['GET'])

def populate_testcases():

conn connection_pool.getconn()

try:

cursor conn.cursor()
cursor.execute("SELECT DISTINCT testcasename FROM Lumos. TESTCASE LIST WHERE Inactiveflag = %s ORDER BY testcasename", ('N'))

testcaseslist = [item[8] for item in cursor.fetchall()]1

return jsonify({"TestcasesList": testcaseslist}), 200

except Exception as e:

return jsonify({'error': f"Failed at populate_testcases: {str(e)}"}), 400

finally:

cursor.close()

connection_pool.putconn(conn)

#API endpoint to retrieve test cases associated with a given test pack and those not yet included in it

@app.route('/api/edit_testpack', methods=['GET'])

def edit_testpack():

testpack_name = request.args.get('testpack name

if not testpack_name:

return jsonify({'error': 'Missing input: Test Pack Name must be specified. '}), 488

conn connection_pool.getconn()

try:

cursor conn.cursor()

#Query 1: Retrieve all test cases currently included in the specified test pack

#Filters out null entries and returns a distinct, alphabetically ordered List
select_query1 =

SELECT DISTINCT testcasename FROM Lumos.TESTPACK LIST WHERE testpack_name %s AND testcasename IS NOT NULL ORDER BY testcasename;

cursor.execute(select_query1, (testpack_name,))

testpack_testcases cursor.fetchall()

#Query 2: Retrieve all active test cases that are NOT part of the specified test pack

# Uses NOT EXISTS for efficient exclusion and ensures only active test cases are returned

select_query2 =

SELECT DISTINCT t2.testcasename FROM Lumos. TESTCASE LIST 12 WHERE 12. Inactiveflag = 'N' AND NOT EXISTS (SELECT 1 FROM Lumos. TESTPACK LIST ti WHERE t1.testpack_name %s AND t1.testcasename ORDER BY 12.testcasename; t2.testcasename)

cursor.execute(select_query2, (testpack_name,))

testcases cursor.fetchall()

response = {

}

'testpack_testcases': [row for row in tes pack testcases),

'testcases': [row for row in testcases]

except Exception as e:

return jsonify({'error': f"Failed at edit testpack: {str(e))"}), 400


#API endpoint to create and save a new Test Pack with selected Test Cases

@app.route('/api/save_testpack', methods=['POST'])

def save_testpack():

data request.json

testpackname data.get('testpackName','').strip()

testcaselist data.get('testcaselist', [])

username data.get('userName','').strip()

if not testpackname:

cursor.close()

return jsonify({'error': 'Test Pack name is a mandatory field.']), 400

if not username:

return jsonify({'error': 'User name is missing. Please refresh the application,), 400

if not testcaselist:

return jsonify({'error': 'Empty test pack. Please add at least one test case. '}), 400

conn connection_pool.getconn()

try:

cursor conn.cursor()

#Check if the Test Pack exists

cursor.execute("SELECT COUNT(*) FROM Lumos.testpack_list WHERE testpack_name %s AND Inactiveflag = %s", (testpackname, 'N'))

if cursor.fetchone() [0] != 0:
return jsonify({'error': f"Testpack (testpackname) already exists."}), 400

if testcaselist:

cursor.executemany (

)

"INSERT INTO lumos.testpack_list (created_by, lastupdby, testpack_name, testcasename, lastupd) VALUES (%s, %s, %s, %s, DATE_TRUNC('second', CURRENT_TIMESTAMP((ייי,

[(username, username, testpackname, tc) for tc in testcaselist]

log_activity(username, action='Create', testcasename='Pack: testpackname, blockname='')

conn.commit()

return jsonify({'message': f"Testpack {testpackname) Created successfully."}), 200

except Exception as e:

return jsonify({'error': f"Failed at save_testpack: {str(e)}"}), 400

finally:

cursor.close()

connection_pool.putconn(conn)

#API to update a Test Pack by replacing its test cases in the Testpack_list table

@app.route('/api/update_testpack', methods=['PUT'])

def update_testpack():

data request.json

testpackname data.get('testpackName','').strip()

newtestcases = data.get('testcaseList', [])

username = data.get('userName','').strip()

if not testpackname:

>

return jsonify({'error': 'Invalid Test Pack selected.'}), 400

if not username:

return jsonify({'error': 'User name is missing. Please refresh the application.'}), 400

conn connection_pool.getconn()

try:

cursor conn.cursor()

#Check if the Test Pack exists

cursor.execute("SELECT COUNT(*) FROM Lumos.testpack_list WHERE testpack_name %s AND Inactiveflag = %s", (testpackname, 'N')) if cursor.fetchone() [0] == 0: return jsonify({'error': f"Test Pack (testpackname) does not exist."}), 400

try:

#Delete existing Test Pack

cursor.execute("DELETE FROM lumos.testpack list WHERE testpack_name %s", (testpackname,))

#Insert all test cases (new and old)

if newtestcases:

cursor.executemany (

'''INSERT INTO Lumos.testpack list (lastupdby, created_by, testpack_name, testcasename, lastupd) VALUES (%s, %s, %s, %s, DATE TRUNC('second', CURRENT_TIMESTAMP))''',
[(username, username, testpackname, tc,) for tc in

newtestcases]

except Exception as error:

conn.rollback() # Rollback in case of error

log_activity(username=username, action='Update failed', testcasename='Pack: + testpackname, blockname='')

return jsonify(" Test Pack Updation Failed!: {}".format(error)), 400

#Log activity

log_activity(username=username, action='Update', testcasename='Pack: testpackname, blockname='')

conn.commit()

return jsonify({'message': f" Test Cases updated for Test Pack (testpackname)."}), 200

except Exception as e:

return jsonify({'error': f"Failed at update testpack: (str(e)}"}), 400

finally:

cursor.close()

connection_pool.putconn (conn)

#API to Soft-delete a Test Pack by marking it inactive in Testpack List tables

@app.route('/api/delete_testpack', methods=['PUT'])

def delete_testpack():

conn connection_pool.getconn()
data request.json

testpackname data.get('testpackName')

username = data.get('userName', '').strip()

if not testpackname or not username:

return jsonify({'error': 'Test Pack Name and User Name are required')}), 400

try:

try:

cursor = conn.cursor()

delete_query='UPDATE lumos.testpack_list SET Inactiveflag = %s, lastupdby = %s, Lastupd DATE_TRUNC('second', CURRENT_TIMESTAMP) WHERE testpack_name %s'

cursor.execute(delete_query, ('Y', username, testpackname))

#Log the deletion activity

log_activity(username=username, action='Delete', testcasename="Pack: testpackname, blockname='")

conn.commit()

return jsonify({'message': f'Testpack (testpackname} deleted successfully'}), 200

except Exception as error:

conn.rollback() # Rollback in case of error

log_activity(username username, action 'Delete failed', testcasename='Pack: testpackname, blockname=)

return jsonify("Testpack deletion Failed!: {}".format(error)), 400
except Exception as e:

return jsonify({'error': f"Failed at delete_testpack: {str(e)}"}), 480

Finally:

cursor.close()

connection_pool.putconn(conn)