import requests
import datetime
import db
import logic

# Abstract base class / interface for verifier
class LeetCodeVerifier:
    def verify(self, username: str) -> list:
        """
        Returns a list of dicts: [{"title": str, "slug": str, "difficulty": str, "timestamp": int}]
        representing accepted solutions solved recently.
        """
        raise NotImplementedError

class GraphQLLeetCodeVerifier(LeetCodeVerifier):
    def verify(self, username: str) -> list:
        if not username:
            return []
            
        url = "https://leetcode.com/graphql"
        # GraphQL query to get recent submissions
        query = """
        query recentAcSubmissions($username: String!, $limit: Int!) {
          recentAcSubmissionList(username: $username, limit: $limit) {
            id
            title
            titleSlug
            timestamp
          }
        }
        """
        variables = {
            "username": username,
            "limit": 15
          }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        
        try:
            r = requests.post(url, json={"query": query, "variables": variables}, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                submissions = data.get("data", {}).get("recentAcSubmissionList", [])
                if not submissions:
                    return []
                
                # Retrieve problem difficulties via single query or dynamic parsing.
                # Since LeetCode graphQL recentAcSubmissionList doesn't contain difficulty,
                # we can fetch details of each unique problem, or default to checking local planner,
                # or query another public endpoint/cache to determine difficulty.
                # Let's write a quick difficulty lookup query.
                verified_problems = []
                for sub in submissions:
                    title = sub["title"]
                    slug = sub["titleSlug"]
                    ts = int(sub["timestamp"])
                    
                    # Get difficulty
                    diff = self.get_problem_difficulty(slug)
                    
                    verified_problems.append({
                        "title": title,
                        "slug": slug,
                        "difficulty": diff,
                        "timestamp": ts
                    })
                return verified_problems
        except Exception as e:
            print(f"Error querying LeetCode GraphQL API: {e}")
            
        return []

    def get_problem_difficulty(self, slug: str) -> str:
        # Check database settings or default to Medium if query fails
        # Let's run a quick GraphQL call for problem details
        url = "https://leetcode.com/graphql"
        query = """
        query questionTitle($titleSlug: String!) {
          question(titleSlug: $titleSlug) {
            difficulty
          }
        }
        """
        variables = {"titleSlug": slug}
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        try:
            r = requests.post(url, json={"query": query, "variables": variables}, headers=headers, timeout=5)
            if r.status_code == 200:
                data = r.json()
                diff = data.get("data", {}).get("question", {}).get("difficulty")
                if diff in ["Easy", "Medium", "Hard"]:
                    return diff
        except Exception:
            pass
        return "Medium" # fallback default

def sync_leetcode_submissions():
    username = db.get_setting("leetcode_username", "")
    if not username:
        return
        
    verifier = GraphQLLeetCodeVerifier()
    submissions = verifier.verify(username)
    if not submissions:
        return
        
    # Get today's local date range in unix timestamps
    today_start = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    today_start_ts = int(today_start.timestamp())
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    for sub in submissions:
        # Check if timestamp is today
        if sub["timestamp"] >= today_start_ts:
            # Check if we already registered this URL/Slug
            slug = sub["slug"]
            url = f"https://leetcode.com/problems/{slug}/"
            
            cursor.execute("SELECT id FROM problems WHERE url = ? OR url = ?", (url, url[:-1]))
            exists = cursor.fetchone()
            
            if not exists:
                # Add to local DB as verified solving
                db.get_connection().close() # close before invoking logic helper
                logic.add_problem(
                    name=sub["title"],
                    url=url,
                    difficulty=sub["difficulty"],
                    date_solved=logic.get_today_date_str(),
                    verified=1
                )
                
    if conn:
        conn.close()

if __name__ == "__main__":
    # Test submission fetching if username is set
    import sys
    if len(sys.argv) > 1:
        test_user = sys.argv[1]
        print(f"Testing LeetCode fetch for: {test_user}")
        v = GraphQLLeetCodeVerifier()
        res = v.verify(test_user)
        for r in res:
            print(f"- {r['title']} ({r['difficulty']}) solved at {datetime.datetime.fromtimestamp(r['timestamp'])}")
