// Simple synchronous approach
use rusqlite::{Connection, Result};

#[derive(Debug)]
struct Artist {
    name: String,
    channel_name: String,
    subscriber_count: Option<i64>,
}

fn get_top_artists(conn: &Connection, limit: i32) -> Result<Vec<Artist>> {
    let mut stmt = conn.prepare(
        "SELECT artist_name, channel_name, subscriber_count 
         FROM artist_cache 
         ORDER BY subscriber_count DESC 
         LIMIT ?1"
    )?;
    
    let artists = stmt.query_map([limit], |row| {
        Ok(Artist {
            name: row.get(0)?,
            channel_name: row.get(1)?,
            subscriber_count: row.get(2)?,
        })
    })?;
    
    artists.collect()
}
