-- Link surrogate keys.

UPDATE Education ED
SET userId = EN.id
FROM Entities EN
WHERE EN.facebookId = ED.userFacebookId
;

UPDATE Education ED
SET schoolId = EN.id
FROM Entities EN
WHERE EN.facebookId = ED.schoolFacebookId
;

UPDATE Employment EM
SET userId = EN.id
FROM Entities EN
WHERE EN.facebookId = EM.userFacebookId
;

UPDATE Employment EM
SET workId = EN.id
FROM Entities EN
WHERE EN.facebookId = EM.workFacebookId
;

UPDATE Lived L
SET userId = EN.id
FROM Entities EN
WHERE EN.facebookId = L.userFacebookId
;

UPDATE Lived L
SET placeId = EN.id
FROM Entities EN
WHERE EN.facebookId = L.placeFacebookId
;

-- Drop redundant facebook ids.
ALTER TABLE Education
DROP COLUMN userFacebookId,
DROP COLUMN schoolFacebookId
;

ALTER TABLE Employment
DROP COLUMN userFacebookId,
DROP COLUMN workFacebookId
;

ALTER TABLE Lived
DROP COLUMN userFacebookId,
DROP COLUMN placeFacebookId
;

-- Indexes

-- Key up the foreign keys.
CREATE INDEX IX_Education_userId ON Education (userId);
CREATE INDEX IX_Education_schoolId ON Education (schoolId);

CREATE INDEX IX_Employment_userId ON Employment (userId);
CREATE INDEX IX_Employment_workId ON Employment (workId);

CREATE INDEX IX_Lived_userId ON Lived (userId);
CREATE INDEX IX_Lived_workId ON Lived (placeId);

CREATE INDEX IX_Entities_name_id ON Entities (name, id);

-- Post-processing
UPDATE Entities EN
SET isSchool = TRUE
FROM Education ED
WHERE ED.schoolId = EN.id
;

UPDATE Entities EN
SET isWork = TRUE
FROM Employment EM
WHERE EM.workId = EN.id
;

UPDATE Entities EN
SET isPlace = TRUE
FROM Lived L
WHERE L.placeId = EN.id
;

UPDATE Entities EN
SET isPerson = NOT (isPlace OR isWork OR isSchool)
;

-- More indexes.
CREATE INDEX IX_Entities_id_person ON Entities (id, isPerson);
