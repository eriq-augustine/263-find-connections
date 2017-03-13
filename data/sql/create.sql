DROP TABLE IF EXISTS Edges;
DROP TABLE IF EXISTS Lived;
DROP TABLE IF EXISTS Employment;
DROP TABLE IF EXISTS Education;
DROP TABLE IF EXISTS Entities;

CREATE TABLE Entities (
   id SERIAL CONSTRAINT PK_Entities_id PRIMARY KEY,
   facebookId TEXT NOT NULL,
   name TEXT NOT NULL,
   isPage BOOLEAN NOT NULL DEFAULT FALSE,
   isSchool BOOLEAN NOT NULL DEFAULT FALSE, -- Will get populated during optimization.
   isPlace BOOLEAN NOT NULL DEFAULT FALSE, -- Will get populated during optimization.
   isWork BOOLEAN NOT NULL DEFAULT FALSE, -- Will get populated during optimization.
   isPerson BOOLEAN NOT NULL DEFAULT FALSE, -- Will get populated during optimization.
   imageUrl TEXT,
   imageBase64 TEXT,
   CONSTRAINT UQ_Entities_facebookId UNIQUE(facebookId)
);

CREATE TABLE Education (
   id SERIAL CONSTRAINT PK_Education_id PRIMARY KEY,
   userId INT REFERENCES Entities,
   schoolId INT REFERENCES Entities,
   position TEXT,
   userFacebookId TEXT NOT NULL, -- Will get dropped after surrogate key linking.
   schoolFacebookId TEXT NOT NULL -- Will get dropped after surrogate key linking.
);

CREATE TABLE Employment (
   id SERIAL CONSTRAINT PK_Employment_id PRIMARY KEY,
   userId INT REFERENCES Entities,
   workId INT REFERENCES Entities,
   position TEXT,
   userFacebookId TEXT NOT NULL, -- Will get dropped after surrogate key linking.
   workFacebookId TEXT NOT NULL -- Will get dropped after surrogate key linking.
);

CREATE TABLE Lived (
   id SERIAL CONSTRAINT PK_Lived_id PRIMARY KEY,
   userId INT REFERENCES Entities,
   placeId INT REFERENCES Entities,
   position TEXT,
   userFacebookId TEXT NOT NULL, -- Will get dropped after surrogate key linking.
   placeFacebookId TEXT NOT NULL -- Will get dropped after surrogate key linking.
);

-- Undirected
-- Semetric edges will be included for speed.
CREATE TABLE Edges (
   id SERIAL CONSTRAINT PK_Edges_id PRIMARY KEY,
   fromEntityId INT REFERENCES Entities NOT NULL,
   toEntityId INT REFERENCES Entities NOT NULL,
   score INT NOT NULL,
   isInner BOOLEAN NOT NULL, -- "Inner" edges are only between people.
   CONSTRAINT UQ_Edges_fromEntityId_toEntityId UNIQUE(fromEntityId, toEntityId)
);
