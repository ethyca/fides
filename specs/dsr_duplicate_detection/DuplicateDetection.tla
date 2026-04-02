---- MODULE DuplicateDetection ----
(***********************************************************************)
(* TLA+ specification for duplicate detection race condition           *)
(*                                                                     *)
(* SYSTEM:   Privacy Request Duplicate Detection                       *)
(* MODULES:  src/fides/api/service/privacy_request/duplication_detection.py *)
(*           src/fides/service/privacy_request/privacy_request_service.py   *)
(*           src/fides/api/v1/endpoints/privacy_request_endpoints.py        *)
(*           src/fides/api/service/privacy_request/request_service.py       *)
(* TICKET:   ENG-2474                                                  *)
(* CREATED:  2026-03-27                                                *)
(*                                                                     *)
(* Models the interaction between:                                     *)
(*   - DataSubject: submits DSRs and enters verification codes         *)
(*   - DuplicateCheck: runs check_for_duplicates at creation and       *)
(*                     at identity verification time                   *)
(*   - RequeueWatchdog: requeue_interrupted_tasks Celery beat that     *)
(*                      can re-process stale requests                  *)
(*                                                                     *)
(* BUG BEING MODELED (ENG-2474):                                       *)
(*   User submits DSR#1 -> enters wrong verification code ->           *)
(*   submits DSR#2 (same identity) -> verifies DSR#2 correctly.       *)
(*   Both requests appear in Request Manager in different statuses     *)
(*   ("requires_input" and "unverified") because duplicate detection   *)
(*   at creation/verify time doesn't catch all interleavings, and      *)
(*   the requeue watchdog has no duplicate check at all.               *)
(*                                                                     *)
(* TWO BUGS FOUND:                                                     *)
(*   1. DupCheck has no tiebreaker when both verified (FixedDupCheck)  *)
(*   2. Verification can overwrite "duplicate" status (FixedDupCheck)  *)
(*                                                                     *)
(* NOTE: The requeue watchdog does NOT need a dup check because        *)
(* is_duplicate_request early-returns False for ACTIONED requests      *)
(* (line 383 of duplication_detection.py). All requests selected by    *)
(* requeue_interrupted_tasks are ACTIONED, so the check is a no-op.   *)
(* The model captures this via the ACTIONED guard in DupCheckStatus.   *)
(*                                                                     *)
(* APPROACH: Use a single operator DupCheck(req) that models the       *)
(*   check_for_duplicates logic as an atomic DB transaction. Each      *)
(*   call site invokes it via a labeled step (one atomic action).      *)
(*                                                                     *)
(* KEY INVARIANTS:                                                     *)
(*   AtMostOneActivePerIdentity - at most one non-duplicate request    *)
(*     per identity+policy is actively processing at any time          *)
(*   DuplicateConsistency - if A is marked duplicate of B,             *)
(*     then B must not also be marked duplicate                        *)
(*                                                                     *)
(* NOT MODELED:                                                        *)
(*   - Multiple identities / policies (one identity group suffices)    *)
(*   - Full DSR execution pipeline (abstracted to "processing")       *)
(*   - Manual approval flow (orthogonal to duplicate detection)        *)
(*   - Time window expiry on duplicate groups                          *)
(***********************************************************************)

EXTENDS TLC, Integers, FiniteSets

CONSTANTS
    NumRequests,        \* Number of DSRs the data subject can submit (2-3)
    MaxVerifyAttempts,  \* Max wrong codes before giving up on a request (1-2)
    FixedDupCheck       \* TRUE = fix dup check tiebreaker + verify guard

Requests == 1..NumRequests

\* Request statuses (subset of PrivacyRequestStatus relevant to this flow)
STATUSES == {
    "none",             \* not yet submitted
    "unverified",       \* identity_unverified -- just created, awaiting code
    "pending",          \* pending -- verified, awaiting approval
    "duplicate",        \* marked as duplicate by check_for_duplicates
    "approved",         \* approved -- ready to be queued for processing
    "in_processing",    \* actively being processed by a Celery worker
    "complete"          \* terminal: processing finished
}

TERMINAL == {"complete", "duplicate"}

\* Statuses that count as "actively processing" for duplicate detection
\* Maps to ACTIONED_REQUEST_STATUSES in duplication_detection.py
ACTIONED == {"approved", "in_processing"}

\* ---------------------------------------------------------------
\* DupCheck operator: models check_for_duplicates as a pure function
\* Returns the new status and canonical arrays after running the check.
\*
\* Logic (from duplication_detection.py:is_duplicate_request):
\* 0a. If req is ACTIONED, return unchanged (early-return, line 383)
\* 0b. If req is already duplicate, return unchanged (early-return, line 398)
\* 1. Find "others" = submitted, non-duplicate, non-terminal requests
\* 2. If any other is ACTIONED, mark req as duplicate
\* 3. If any other is verified and req is not, mark req as duplicate
\* 4. If req is verified and no other is, mark others as duplicate
\* 5. If neither verified, oldest (smallest ID) wins
\* 6. (FIX) If both verified, oldest wins (requires FixedDupCheck)
\* ---------------------------------------------------------------

Others(req, st) ==
    {r \in Requests : r /= req
                      /\ st[r] /= "none"
                      /\ st[r] /= "duplicate"
                      /\ st[r] /= "complete"}

DupCheckStatus(req, st, ver, can) ==
    \* Rule 0a: ACTIONED requests are never duplicates (early-return, line 383)
    IF st[req] \in ACTIONED THEN <<st, can>>
    \* Rule 0b: Already-duplicate requests return early (line 398)
    ELSE IF st[req] = "duplicate" THEN <<st, can>>
    ELSE LET oth == Others(req, st) IN
    IF oth = {} THEN <<st, can>>
    \* Rule 1: other is actioned => this is duplicate
    ELSE IF \E r \in oth : st[r] \in ACTIONED THEN
        LET dup == CHOOSE r \in oth : st[r] \in ACTIONED IN
        << [st EXCEPT ![req] = "duplicate"],
           [r \in Requests |-> IF r = req THEN dup
                               ELSE IF can[r] = req THEN dup
                               ELSE can[r]] >>
    \* Rule 2: other is verified, this is not => this is duplicate
    ELSE IF \E r \in oth : ver[r] = TRUE /\ ver[req] = FALSE THEN
        LET dup == CHOOSE r \in oth : ver[r] = TRUE IN
        << [st EXCEPT ![req] = "duplicate"],
           [r \in Requests |-> IF r = req THEN dup
                               ELSE IF can[r] = req THEN dup
                               ELSE can[r]] >>
    \* Rule 3: this is verified, others are not => mark others as duplicate
    ELSE IF ver[req] = TRUE /\ \A r \in oth : ver[r] = FALSE THEN
        << [r \in Requests |-> IF r \in oth THEN "duplicate" ELSE st[r]],
           [r \in Requests |-> IF r \in oth THEN req
                               ELSE IF can[r] /= 0 /\ can[r] \in oth THEN req
                               ELSE can[r]] >>
    \* Rule 4: neither verified => oldest (smallest ID) wins
    ELSE IF ver[req] = FALSE /\ \A r \in oth : ver[r] = FALSE THEN
        LET all == oth \union {req} IN
        LET oldest == CHOOSE r \in all : \A r2 \in all : r <= r2 IN
        IF oldest /= req THEN
            << [st EXCEPT ![req] = "duplicate"],
               [r \in Requests |-> IF r = req THEN oldest
                                   ELSE IF can[r] = req THEN oldest
                                   ELSE can[r]] >>
        ELSE <<st, can>>
    \* Rule 5 (FIX): both verified, neither actioned => oldest wins
    \* Without this, two simultaneously-verified requests both survive
    ELSE IF FixedDupCheck THEN
        LET all == oth \union {req} IN
        LET oldest == CHOOSE r \in all : \A r2 \in all : r <= r2 IN
        IF oldest /= req THEN
            << [st EXCEPT ![req] = "duplicate"],
               [r \in Requests |-> IF r = req THEN oldest
                                   ELSE IF can[r] = req THEN oldest
                                   ELSE can[r]] >>
        ELSE <<st, can>>
    ELSE <<st, can>>

(* --algorithm DuplicateDetection

variables
    status = [r \in Requests |-> "none"],
    verified = [r \in Requests |-> FALSE],
    verifyAttempts = [r \in Requests |-> 0],
    canonical = [r \in Requests |-> 0],
    submitted = 0;

\* ---------------------------------------------------------------
\* Data Subject: submits requests sequentially
\* ---------------------------------------------------------------
fair process DataSubject = 0
variables nextReq = 1;
begin
    DSLoop:
        while nextReq <= NumRequests do
            SubmitRequest:
                status[nextReq] := "unverified";
                submitted := submitted + 1;
            \* check_for_duplicates at creation (privacy_request_service.py:472)
            DupCheckCreate:
                with result = DupCheckStatus(nextReq, status, verified, canonical) do
                    status := result[1];
                    canonical := result[2];
                end with;
                nextReq := nextReq + 1;
        end while;
end process;

\* ---------------------------------------------------------------
\* Verifier: one per request, enters verification codes
\* ---------------------------------------------------------------
fair process Verifier \in Requests
begin
    VerifyWait:
        await status[self] = "unverified";
    TryVerify:
        either
            \* Wrong code path
            WrongCode:
                if verifyAttempts[self] < MaxVerifyAttempts then
                    verifyAttempts[self] := verifyAttempts[self] + 1;
                    goto VerifyWait;
                end if;
                \* else: exhausted attempts, request stays unverified
        or
            \* Correct code: verify identity, transition to pending
            \* FIX: guard prevents overwriting "duplicate" with "pending"
            CorrectCode:
                if FixedDupCheck => status[self] = "unverified" then
                    verified[self] := TRUE;
                    status[self] := "pending";
                end if;
            \* handle_approval -> check_for_duplicates (privacy_request_service.py:1204)
            DupCheckVerify:
                with result = DupCheckStatus(self, status, verified, canonical) do
                    status := result[1];
                    canonical := result[2];
                end with;
            \* If not marked duplicate, auto-approve
            AutoApprove:
                if status[self] = "pending" then
                    status[self] := "approved";
                end if;
        end either;
end process;

\* ---------------------------------------------------------------
\* Processor: Celery worker that processes approved requests
\* ---------------------------------------------------------------
fair process Processor \in {100 + r : r \in Requests}
variables procReq = self - 100;
begin
    WaitApproved:
        await status[procReq] = "approved";
    StartProcessing:
        status[procReq] := "in_processing";
    FinishProcessing:
        status[procReq] := "complete";
end process;

\* ---------------------------------------------------------------
\* Requeue Watchdog: requeue_interrupted_tasks Celery beat
\*
\* In the real system this fires periodically and re-queues
\* requests whose Celery tasks disappeared (worker crash, etc).
\* We model it as nondeterministically picking any "stuck" request.
\*
\* No duplicate check here: all requeued requests are ACTIONED,
\* and is_duplicate_request early-returns False for ACTIONED
\* requests (duplication_detection.py:383). The ACTIONED guard
\* in DupCheckStatus captures this.
\* ---------------------------------------------------------------
fair process RequeueWatchdog = 200
begin
    WatchdogLoop:
        while TRUE do
            WatchdogPick:
                skip;
        end while;
end process;

end algorithm; *)

\* BEGIN TRANSLATION (chksum(pcal) = "83b26ef3" /\ chksum(tla) = "7d1b80d3")
VARIABLES pc, status, verified, verifyAttempts, canonical, submitted, nextReq, 
          procReq

vars == << pc, status, verified, verifyAttempts, canonical, submitted, 
           nextReq, procReq >>

ProcSet == {0} \cup (Requests) \cup ({100 + r : r \in Requests}) \cup {200}

Init == (* Global variables *)
        /\ status = [r \in Requests |-> "none"]
        /\ verified = [r \in Requests |-> FALSE]
        /\ verifyAttempts = [r \in Requests |-> 0]
        /\ canonical = [r \in Requests |-> 0]
        /\ submitted = 0
        (* Process DataSubject *)
        /\ nextReq = 1
        (* Process Processor *)
        /\ procReq = [self \in {100 + r : r \in Requests} |-> self - 100]
        /\ pc = [self \in ProcSet |-> CASE self = 0 -> "DSLoop"
                                        [] self \in Requests -> "VerifyWait"
                                        [] self \in {100 + r : r \in Requests} -> "WaitApproved"
                                        [] self = 200 -> "WatchdogLoop"]

DSLoop == /\ pc[0] = "DSLoop"
          /\ IF nextReq <= NumRequests
                THEN /\ pc' = [pc EXCEPT ![0] = "SubmitRequest"]
                ELSE /\ pc' = [pc EXCEPT ![0] = "Done"]
          /\ UNCHANGED << status, verified, verifyAttempts, canonical, 
                          submitted, nextReq, procReq >>

SubmitRequest == /\ pc[0] = "SubmitRequest"
                 /\ status' = [status EXCEPT ![nextReq] = "unverified"]
                 /\ submitted' = submitted + 1
                 /\ pc' = [pc EXCEPT ![0] = "DupCheckCreate"]
                 /\ UNCHANGED << verified, verifyAttempts, canonical, nextReq, 
                                 procReq >>

DupCheckCreate == /\ pc[0] = "DupCheckCreate"
                  /\ LET result == DupCheckStatus(nextReq, status, verified, canonical) IN
                       /\ status' = result[1]
                       /\ canonical' = result[2]
                  /\ nextReq' = nextReq + 1
                  /\ pc' = [pc EXCEPT ![0] = "DSLoop"]
                  /\ UNCHANGED << verified, verifyAttempts, submitted, procReq >>

DataSubject == DSLoop \/ SubmitRequest \/ DupCheckCreate

VerifyWait(self) == /\ pc[self] = "VerifyWait"
                    /\ status[self] = "unverified"
                    /\ pc' = [pc EXCEPT ![self] = "TryVerify"]
                    /\ UNCHANGED << status, verified, verifyAttempts, 
                                    canonical, submitted, nextReq, procReq >>

TryVerify(self) == /\ pc[self] = "TryVerify"
                   /\ \/ /\ pc' = [pc EXCEPT ![self] = "WrongCode"]
                      \/ /\ pc' = [pc EXCEPT ![self] = "CorrectCode"]
                   /\ UNCHANGED << status, verified, verifyAttempts, canonical, 
                                   submitted, nextReq, procReq >>

WrongCode(self) == /\ pc[self] = "WrongCode"
                   /\ IF verifyAttempts[self] < MaxVerifyAttempts
                         THEN /\ verifyAttempts' = [verifyAttempts EXCEPT ![self] = verifyAttempts[self] + 1]
                              /\ pc' = [pc EXCEPT ![self] = "VerifyWait"]
                         ELSE /\ pc' = [pc EXCEPT ![self] = "Done"]
                              /\ UNCHANGED verifyAttempts
                   /\ UNCHANGED << status, verified, canonical, submitted, 
                                   nextReq, procReq >>

CorrectCode(self) == /\ pc[self] = "CorrectCode"
                     /\ IF FixedDupCheck => status[self] = "unverified"
                           THEN /\ verified' = [verified EXCEPT ![self] = TRUE]
                                /\ status' = [status EXCEPT ![self] = "pending"]
                           ELSE /\ TRUE
                                /\ UNCHANGED << status, verified >>
                     /\ pc' = [pc EXCEPT ![self] = "DupCheckVerify"]
                     /\ UNCHANGED << verifyAttempts, canonical, submitted, 
                                     nextReq, procReq >>

DupCheckVerify(self) == /\ pc[self] = "DupCheckVerify"
                        /\ LET result == DupCheckStatus(self, status, verified, canonical) IN
                             /\ status' = result[1]
                             /\ canonical' = result[2]
                        /\ pc' = [pc EXCEPT ![self] = "AutoApprove"]
                        /\ UNCHANGED << verified, verifyAttempts, submitted, 
                                        nextReq, procReq >>

AutoApprove(self) == /\ pc[self] = "AutoApprove"
                     /\ IF status[self] = "pending"
                           THEN /\ status' = [status EXCEPT ![self] = "approved"]
                           ELSE /\ TRUE
                                /\ UNCHANGED status
                     /\ pc' = [pc EXCEPT ![self] = "Done"]
                     /\ UNCHANGED << verified, verifyAttempts, canonical, 
                                     submitted, nextReq, procReq >>

Verifier(self) == VerifyWait(self) \/ TryVerify(self) \/ WrongCode(self)
                     \/ CorrectCode(self) \/ DupCheckVerify(self)
                     \/ AutoApprove(self)

WaitApproved(self) == /\ pc[self] = "WaitApproved"
                      /\ status[procReq[self]] = "approved"
                      /\ pc' = [pc EXCEPT ![self] = "StartProcessing"]
                      /\ UNCHANGED << status, verified, verifyAttempts, 
                                      canonical, submitted, nextReq, procReq >>

StartProcessing(self) == /\ pc[self] = "StartProcessing"
                         /\ status' = [status EXCEPT ![procReq[self]] = "in_processing"]
                         /\ pc' = [pc EXCEPT ![self] = "FinishProcessing"]
                         /\ UNCHANGED << verified, verifyAttempts, canonical, 
                                         submitted, nextReq, procReq >>

FinishProcessing(self) == /\ pc[self] = "FinishProcessing"
                          /\ status' = [status EXCEPT ![procReq[self]] = "complete"]
                          /\ pc' = [pc EXCEPT ![self] = "Done"]
                          /\ UNCHANGED << verified, verifyAttempts, canonical, 
                                          submitted, nextReq, procReq >>

Processor(self) == WaitApproved(self) \/ StartProcessing(self)
                      \/ FinishProcessing(self)

WatchdogLoop == /\ pc[200] = "WatchdogLoop"
                /\ pc' = [pc EXCEPT ![200] = "WatchdogPick"]
                /\ UNCHANGED << status, verified, verifyAttempts, canonical, 
                                submitted, nextReq, procReq >>

WatchdogPick == /\ pc[200] = "WatchdogPick"
                /\ TRUE
                /\ pc' = [pc EXCEPT ![200] = "WatchdogLoop"]
                /\ UNCHANGED << status, verified, verifyAttempts, canonical,
                                submitted, nextReq, procReq >>

RequeueWatchdog == WatchdogLoop \/ WatchdogPick

Next == DataSubject \/ RequeueWatchdog
           \/ (\E self \in Requests: Verifier(self))
           \/ (\E self \in {100 + r : r \in Requests}: Processor(self))

Spec == /\ Init /\ [][Next]_vars
        /\ WF_vars(DataSubject)
        /\ \A self \in Requests : WF_vars(Verifier(self))
        /\ \A self \in {100 + r : r \in Requests} : WF_vars(Processor(self))
        /\ WF_vars(RequeueWatchdog)

\* END TRANSLATION

\* ---------------------------------------------------------------
\* Invariants
\* ---------------------------------------------------------------

TypeOK ==
    /\ \A r \in Requests : status[r] \in STATUSES
    /\ \A r \in Requests : verified[r] \in BOOLEAN
    /\ \A r \in Requests : verifyAttempts[r] \in 0..MaxVerifyAttempts
    /\ \A r \in Requests : canonical[r] = 0 \/ canonical[r] \in Requests
    /\ submitted \in 0..NumRequests

\* KEY INVARIANT: at most one request per identity actively processing
AtMostOneActivePerIdentity ==
    Cardinality({r \in Requests : status[r] \in ACTIONED}) <= 1

\* If A is duplicate of B, B must not also be duplicate
DuplicateConsistency ==
    \A r \in Requests :
        (status[r] = "duplicate" /\ canonical[r] /= 0)
            => status[canonical[r]] /= "duplicate"

\* A duplicate's canonical must point to a real, non-none request
DuplicatePointsToLive ==
    \A r \in Requests :
        canonical[r] /= 0
            => (canonical[r] /= r /\ status[canonical[r]] /= "none")

\* ---------------------------------------------------------------
\* Liveness
\* ---------------------------------------------------------------

\* Every verified request eventually reaches terminal or actioned state
VerifiedRequestProgress ==
    \A r \in Requests :
        (verified[r] = TRUE) ~> (status[r] \in TERMINAL \union ACTIONED)

====
