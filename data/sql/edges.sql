-- Put in the known relations with a very high weight.

INSERT INTO Edges
   (fromEntityId, toEntityId, score, isInner)
SELECT DISTINCT
   userId,
   workId,
   100,
   FALSE
FROM Employment
;

-- Symmetric
INSERT INTO Edges
   (fromEntityId, toEntityId, score, isInner)
SELECT DISTINCT
   workId,
   userId,
   100,
   FALSE
FROM Employment
;

INSERT INTO Edges
   (fromEntityId, toEntityId, score, isInner)
SELECT DISTINCT
   userId,
   schoolId,
   100,
   FALSE
FROM Education
ON CONFLICT DO NOTHING -- It is possible for someone to study and work at a school
;

-- Symmetric
INSERT INTO Edges
   (fromEntityId, toEntityId, score, isInner)
SELECT DISTINCT
   schoolId,
   userId,
   100,
   FALSE
FROM Education
ON CONFLICT DO NOTHING -- It is possible for someone to study and work at a school
;

INSERT INTO Edges
   (fromEntityId, toEntityId, score, isInner)
SELECT DISTINCT
   userId,
   placeId,
   100,
   FALSE
FROM Lived
ON CONFLICT DO NOTHING -- It is possible for someone to live in and work for a town.
;

-- Symmetric
INSERT INTO Edges
   (fromEntityId, toEntityId, score, isInner)
SELECT DISTINCT
   placeId,
   userId,
   100,
   FALSE
FROM Lived
ON CONFLICT DO NOTHING -- It is possible for someone to live in and work for a town.
;

-- Inner edges (between people).
-- For each cooccurence of a pair of people, add one to their score.

-- This should also capture symmetric links.
INSERT INTO Edges AS E
   (fromEntityId, toEntityId, score, isInner)
SELECT DISTINCT
   EM1.userId,
   EM2.userId,
   1,
   TRUE
FROM
   Employment EM1
   JOIN Employment EM2 ON EM2.workId = EM1.workId
WHERE EM1.userId != EM2.userId
ON CONFLICT ON CONSTRAINT UQ_Edges_fromEntityId_toEntityId DO UPDATE SET score = E.score + 1
;

INSERT INTO Edges AS E
   (fromEntityId, toEntityId, score, isInner)
SELECT DISTINCT
   ED1.userId,
   ED2.userId,
   1,
   TRUE
FROM
   Education ED1
   JOIN Education ED2 ON ED2.schoolId = ED1.schoolId
WHERE ED1.userId != ED2.userId
ON CONFLICT ON CONSTRAINT UQ_Edges_fromEntityId_toEntityId DO UPDATE SET score = E.score + 1
;

INSERT INTO Edges AS E
   (fromEntityId, toEntityId, score, isInner)
SELECT DISTINCT
   L1.userId,
   L2.userId,
   1,
   TRUE
FROM
   Lived L1
   JOIN Lived L2 ON L2.placeId = L1.placeId
WHERE L1.userId != L2.userId
ON CONFLICT ON CONSTRAINT UQ_Edges_fromEntityId_toEntityId DO UPDATE SET score = E.score + 1
;

CREATE INDEX IX_Edges_fromEntityId_toEntityId_score_isInner ON Edges (fromEntityId, toEntityId, score, isInner);
CREATE INDEX IX_Edges_score ON Edges (score);
