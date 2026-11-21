# EndolysinDB

**Endolysin and Phage Lytic Protein Activity Database**

EndolysinDB is a Flask-based bioinformatics web application for storing, browsing, and searching endolysins and phage lytic proteins.

The application uses MySQL for data storage, Biopython for protein sequence processing, and HTML, CSS, and JavaScript for the frontend.

## Features

- Dashboard displaying protein and database statistics
- Protein browsing and keyword search
- Detailed protein information and amino acid sequences
- Original FASTA identifiers
- Protein domain annotation images
- Protein structure images
- Database tables for domain annotations, target organisms, activity conditions, and engineered proteins
- SVG domain architecture visualization when valid domain coordinates are available

The initial dataset contains five proteins: LysK, LysGH15, CP1, PlyC, and Art-35.

Some scientific tables may initially be empty until verified biological data is imported.

## Prerequisites

Install the following software before running the project:

- Python 3.10 or newer
- MySQL Server 8.0
- MySQL Workbench (optional)
- Git

## 1. Clone the Repository

Open PowerShell or a terminal.

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

Replace the URL and directory name with your actual GitHub repository details.

## 2. Create a Python Virtual Environment

Run:

```bash
python -m venv venv
```

Activate the environment.

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**

```cmd
venv\Scripts\activate.bat
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

## 3. Install Dependencies

Make sure the virtual environment is activated.

```bash
pip install -r requirements.txt
```

This installs the Python dependencies required by the project.

## 4. Configure MySQL

Start the MySQL server and open MySQL Workbench or another MySQL client.

Create the application database:

```sql
CREATE DATABASE IF NOT EXISTS endolysin_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

The application requires a MySQL account with permission to access this database.

## 5. Create the Environment File

In the root directory of the project, create a file named:

```text
.env
```

Add the following configuration:

```dotenv
DATABASE_URL=mysql+pymysql://root:YOUR_MYSQL_PASSWORD@localhost:3306/endolysin_db
SECRET_KEY=replace-with-a-long-random-secret-key
FLASK_DEBUG=1
```

Replace `YOUR_MYSQL_PASSWORD` with your local MySQL password.

The `SECRET_KEY` should be a long, randomly generated value.

**Important:** The application must be configured to read these environment variable names. Check `config.py` if your implementation uses different names.

If your MySQL password contains special characters such as `@`, `#`, `/`, or `:`, URL-encode them in the database connection string.

### Security

Never commit `.env` to GitHub.

Ensure your `.gitignore` includes:

```gitignore
.env
.env.*
!.env.example
venv/
.venv/
__pycache__/
*.pyc
.pytest_cache/
```

You may create an `.env.example` containing placeholder values so other developers know which variables to configure.

## 6. Initialize the Database Tables

If the repository contains Flask-Migrate migrations, apply them using:

```bash
flask --app app db upgrade
```

This creates or updates the required database tables.

The project uses six main tables:

1. `proteins`
2. `domains`
3. `target_organisms`
4. `activities`
5. `engineering`
6. `structures`

If migrations have not been initialized in the repository, follow the database initialization method implemented in the application rather than running `db init` blindly.

## 7. Import Initial Protein Data

Ensure that the initial FASTA file is available at:

```text
data/sequences/initial_proteins.fasta
```

Run the seed script:

```bash
python seed_data.py
```

This imports the initial protein records into MySQL.

The seed script is designed to avoid creating duplicate protein records when executed multiple times.

Protein annotation and structure images should be placed in the appropriate project data directories.

## 8. Start the Flask Application

Run:

```bash
python run.py
```

If the application starts successfully, open:

**http://localhost:5000**

The dashboard should display the initial five protein records.

## 9. Application Pages

| URL | Description |
|---|---|
| `/` | Dashboard |
| `/proteins` | Browse proteins |
| `/proteins/<id>` | Protein details |
| `/search?q=LysK` | Search proteins |
| `/health` | Application health check |
| `/api/stats` | Database statistics in JSON |

## 10. Project Structure

```text
EndolysinDB/
├── app.py
├── config.py
├── models.py
├── run.py
├── seed_data.py
├── requirements.txt
├── .env
├── .gitignore
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── proteins.html
│   ├── protein_detail.html
│   └── search.html
├── static/
│   ├── css/
│   └── js/
└── data/
    ├── sequences/
    │   └── initial_proteins.fasta
    ├── annotations/
    └── structures/
```

The exact folder structure may include additional files such as database migrations, error templates, and supporting scripts.

## 11. Troubleshooting

### MySQL connection error

Verify that:

- MySQL Server is running.
- The database `endolysin_db` exists.
- The username and password in `.env` are correct.
- MySQL is accessible on port `3306`.

### ModuleNotFoundError

Activate the virtual environment and reinstall dependencies:

```bash
pip install -r requirements.txt
```

### Database tables not found

Apply the existing database migrations:

```bash
flask --app app db upgrade
```

### Dashboard shows zero proteins

Run:

```bash
python seed_data.py
```

Also verify that the application is connecting to the intended database.

### Annotation or structure images are missing

Verify that the image files exist in the expected data directories and that their filenames match the paths stored in the database.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Flask |
| Database | MySQL 8.0 |
| ORM | Flask-SQLAlchemy |
| Migrations | Flask-Migrate |
| Sequence processing | Biopython |
| Frontend | HTML, CSS, JavaScript |
| Templates | Jinja2 |

## Development Status

The initial application supports protein browsing, searching, sequence display, and associated annotation and structure images.

Additional scientific functionality, including structured InterProScan annotation imports, host range analysis, engineered protein information, and sequence similarity search, may be added as verified data becomes available.

## License

License information has not yet been specified.
