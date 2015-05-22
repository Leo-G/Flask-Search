from flask import Blueprint, render_template, request,flash, redirect, url_for
from app.users.models import Sites, SitesSchema, db

users = Blueprint('users', __name__)
#http://marshmallow.readthedocs.org/en/latest/quickstart.html#declaring-schemas
schema = SitesSchema()


#main
@users.route('/search/<int:page>', methods=['GET', 'POST'], )
@users.route('/search', methods=['POST', 'GET'])
def search(page=1):
   results = None
   if request.method == 'POST':
           search_string = request.form['search']
           #results = Sites.query.from_statement(db.text("select * from sites where search @@ to_tsquery(:search)")).params(search=search).all()
           query = Sites.query.search(search_string)
           #query.search('somesearchstring')
           results = query.paginate(page=1, per_page=1, error_out=True)
           
           #paginate(page, per_page=1, error_out=True).search(search).all()
           #results = schema.dump(query, many=True).data
   return render_template('search.html', results=results)
   
#Sites
@users.route('/' )
def user_index():
    print(db.func.to_tsquery("3.4"))
    sites = Sites.query.all()
    results = schema.dump(sites, many=True).data
    return render_template('/users/index.html', results=results)

@users.route('/add' , methods=['POST', 'GET'])
def user_add():
    if request.method == 'POST':
        #Validate form values by de-serializing the request, http://marshmallow.readthedocs.org/en/latest/quickstart.html#validation
        form_errors = schema.validate(request.form.to_dict())
        if not form_errors:
            url = request.form['url']
            content = request.form['content']
            tag = request.form['tag']
            site = Sites(url, content, tag)
            return add(site, success_url = 'users.user_index', fail_url = 'users.user_add')
        else:
           flash(form_errors)

    return render_template('/users/add.html')

@users.route('/update/<int:id>' , methods=['POST', 'GET'])

def user_update (id):
    #Get site by primary key:
    site=Sites.query.get_or_404(id)
    if request.method == 'POST':
        form_errors = schema.validate(request.form.to_dict())
        if not form_errors:
           site.url = request.form['url']
           site.content = request.form['content']
           site.tag = request.form['tag']
           return update(site , id, success_url = 'users.user_index', fail_url = 'users.user_update')
        else:
           flash(form_errors)

    return render_template('/users/update.html', site=site)


@users.route('/delete/<int:id>' , methods=['POST', 'GET'])
def user_delete (id):
     site = Sites.query.get_or_404(id)
     return delete(site, fail_url = 'users.user_index')


#CRUD FUNCTIONS
#Arguments  are data to add, function to redirect to if the add was successful and if not
def add (data, success_url = '', fail_url = ''):
    add = data.add(data)
    #if does not return any error
    if not add :
       flash("Add was successful")
       return redirect(url_for(success_url))
    else:
       message=add
       flash(message)
       return redirect(url_for(fail_url))


def update (data, id, success_url = '', fail_url = ''):

            update=data.update()
            #if does not return any error
            if not update :
              flash("Update was successful")
              return redirect(url_for(success_url))
            else:
               message=update
               flash(message)
               return redirect(url_for(fail_url, id=id))



def delete (data, fail_url=''):
     delete=data.delete(data)
     if not delete :
              flash("Delete was successful")

     else:
          message=delete
          flash(message)
     return redirect(url_for(fail_url))
     
#Create  Triggers and Functions
@users.route('/trigger', methods=['GET'])
def trig():
   SQL_index = db.text("""CREATE INDEX tsv_idx ON sites USING gin(search) """)
   db.engine.execute(SQL_index)
   SQL = db.text("""CREATE OR REPLACE FUNCTION search_trigger() RETURNS trigger AS $$
                begin
                  new.search :=
                    setweight(to_tsvector(coalesce(new.url,'')), 'B') ||
                    setweight(to_tsvector(coalesce(new.content,'')), 'C')||
                    setweight(to_tsvector(coalesce(new.tag,'')), 'A');
                  return new;
                end
                $$ LANGUAGE plpgsql""")
   db.engine.execute(SQL)
   SQL1 = db.text("""CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
               ON sites FOR EACH ROW EXECUTE PROCEDURE search_trigger();""")
   db.engine.execute(SQL1)
   return "Done"
      
 


